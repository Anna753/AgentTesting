from collections import defaultdict
from langchain.agents import Tool, AgentExecutor, BaseSingleActionAgent
from langchain.schema import AgentAction
from trace_abstractor import AgentTraceAbstractor
from trace_analyzer import TraceAnalyzer
from generate_mutants import GenerateMocks
from original_run import OriginalRun
import ast
from agent_trajectory import AgentTrajectory
from collections import defaultdict
import re
from sentence_transformers import SentenceTransformer, util
from collections import Counter


class MockRun():
    
      def __init__(self, agent, tools):
          self.agent = agent
          self.tools = tools
          self.model = SentenceTransformer('all-MiniLM-L6-v2')
          self.global_error_counter = Counter()
          self.mock_generator = GenerateMocks() 

      def run(self,user_input,final_answer,abstract_trace,input_num):
        seen_pairs = set()
        unique_action_inputs = []

        def normalize(text):
              text = text.lower()
              if not isinstance(text, str):
                try:
                    text = str(text)
                except Exception:
                    return "" 
              
              text = re.sub(r'[^\w\s]', '', text)  
              text = re.sub(r'\s+', ' ', text)    
              return text.strip()

        def is_semantically_similar(a, b, threshold=0.5):
            a_norm = normalize(a)
            b_norm = normalize(b)
            emb1 = self.model.encode(a_norm, convert_to_tensor=True)
            emb2 = self.model.encode(b_norm, convert_to_tensor=True)
            sim = util.pytorch_cos_sim(emb1, emb2).item()
            return sim >= threshold

        seen_pairs = []  
        unique_action_inputs = []
        if abstract_trace is not None:
            for step in abstract_trace:
              tool_name = step['Action']
              tool_input = step['Action Input']
              observation = step['Observation']
              is_duplicate = False
              for seen_tool, seen_input in seen_pairs:
                  if tool_name == seen_tool and is_semantically_similar(normalize(tool_input), normalize(seen_input)):
                      is_duplicate = True
                      break

              if not is_duplicate:
                  seen_pairs.append((tool_name, tool_input))
                  unique_action_inputs.append({
                      "tool": tool_name,
                      "input": tool_input,
                      "observation": observation
                  })
            mock_lookup = {}
           
            for pair in unique_action_inputs:
                  obs_ = pair["observation"]
                  if isinstance(obs_, str):
                      try:
                          obs_ = ast.literal_eval(obs_)
                      except Exception as e:
                          print("Failed to parse observation:", e)

                  obs = self.mock_generator.generate_mutants(obs_)
                  mock_lookup[(pair["tool"], pair["input"])] = obs


            mutant_type = ['error','partial response','no response']
            for run_idx in range(len(mutant_type)):
                print(f"\n=== MOCK RUN {run_idx + 1} ===")
                def make_mock_func(tool_name):
                    def mocked(input_str: str):
                        input_norm = normalize(input_str)
                        for (stored_tool, stored_input), variants in mock_lookup.items():
                            if stored_tool == tool_name and is_semantically_similar(normalize(stored_input), input_norm):
                                if run_idx < len(variants):
                                    return variants[run_idx]
                                else:
                                    return "Error: Not enough variants"
                        return "Error: unexpected tool input" if mutant_type[run_idx] == "error" else ""
                    return mocked

             
                mocked_tools = []
                for original_tool in self.tools:
                    mocked_func = make_mock_func(original_tool.name)
                    mocked_tools.append(Tool(
                        name=original_tool.name,
                        func=mocked_func,
                        description=original_tool.description
                    ))
              
                if isinstance(self.agent, AgentExecutor):
                    mocked_executor = AgentExecutor.from_agent_and_tools(
                      agent=self.agent.agent,
                      tools=mocked_tools,
                      verbose=True,
                      handle_parsing_errors=True,
                      return_intermediate_steps=True,
                      max_iterations=10
                  )
                    
                elif isinstance(self.agent, BaseSingleActionAgent):
                  mocked_executor = AgentExecutor.from_agent_and_tools(
                      agent=self.agent,
                      tools=mocked_tools,
                      verbose=True,
                      handle_parsing_errors=True,
                      return_intermediate_steps=True,
                      max_iterations=10
                  )

                try:
                    mock_response = mocked_executor.invoke({"input": user_input})
                    mock_intermediate_steps = mock_response.get("intermediate_steps", [])
                    abstractor = AgentTraceAbstractor()
                    abstractor.process_intermediate_steps(mock_intermediate_steps,mutant_type[run_idx])
                    abstract_trace = abstractor.get_abstract_trace()
                    trace_analyzer = TraceAnalyzer(user_input=user_input, final_answer=str(mock_response["output"]),tools=self.tools,mode='mock')
                    trajectory = AgentTrajectory()
                    trajectory.get_trajetory(user_input,1,input_num,mock_intermediate_steps,mock_response["output"])


                    analysis_messages = trace_analyzer.analyze_trace(abstract_trace)
                    print(f"Analysis [Mock {run_idx + 1}]:", analysis_messages)
                    for msg in analysis_messages:
                        self.global_error_counter[((mutant_type[run_idx],), msg)] += 1
                   
                except Exception as e:
                    print(f"Error in mock run {run_idx + 1}: {e}")
                    for msg in analysis_messages:
                        self.global_error_counter[((mutant_type[run_idx],), msg)] += 1

        print("\n=== Overall Error Summary Across All Mock Runs ===")
        for (mutant_type, error_msg), count in self.global_error_counter.items():
             print(f"- [Mutant Type: {', '.join(mutant_type)}] {error_msg}: {count} time(s)")

        return self.global_error_counter