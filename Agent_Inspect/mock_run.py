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
import random
import json
from langchain.prompts.prompt import PromptTemplate


class MockRun:
    def __init__(self, agent, tools, real_prob=0.5, seed=42):
        self.agent = agent
        self.tools = tools
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.global_error_counter = Counter()
        self.mock_generator = GenerateMocks()
        self.real_prob = real_prob
        self.rng = random.Random(seed)

    def run(self, user_input, final_answer, abstract_trace, input_num):
        def normalize(text):
            if not isinstance(text, str):
                try:
                    text = str(text)
                except Exception:
                    return ""
            text = text.lower()
            text = re.sub(r'[^\w\s]', '', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()

        def format_tool_output(value):
            if value is None:
                return ""
            if isinstance(value, (dict, list)):
                try:
                    return json.dumps(value)
                except Exception:
                    return str(value)
            return str(value)

        def is_semantically_similar(a, b, threshold=0.5):
            a_norm = normalize(a)
            b_norm = normalize(b)

            if not a_norm or not b_norm:
                return False

            emb1 = self.model.encode(a_norm, convert_to_tensor=True)
            emb2 = self.model.encode(b_norm, convert_to_tensor=True)
            sim = util.pytorch_cos_sim(emb1, emb2).item()
            return sim >= threshold

        if abstract_trace is None:
            print("Abstract trace is None. Skipping mock runs.")
            return self.global_error_counter

    
        seen_pairs = []
        unique_action_inputs = []

        for step in abstract_trace:
            tool_name = step.get("Action", "")
            tool_input = step.get("Action Input", "")
            observation = step.get("Observation", "")

            is_duplicate = False
            for seen_tool, seen_input in seen_pairs:
                if tool_name == seen_tool and is_semantically_similar(tool_input, seen_input):
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
                parsed_obs = obs_
                try:
                    parsed_obs = ast.literal_eval(obs_)
                except Exception:
                    parsed_obs = obs_
                obs_ = parsed_obs

            variants = self.mock_generator.generate_mutants(
                obs_,
                key=(pair["tool"], pair["input"])
            )

            mock_lookup[(pair["tool"], pair["input"])] = {
                "original": obs_,
                "mutants": variants
            }

        mutant_type = ['error', 'partial response', 'no response', 'delayed response', 'real/simulated']

        for run_idx in range(len(mutant_type)):
            first_real_by_tool = {}
            print(f"\n=== MOCK RUN {run_idx + 1}: {mutant_type[run_idx]} ===")

            def make_mock_func(tool_name):
                def mocked(input_str: str):
                    input_norm = normalize(input_str)

                    for (stored_tool, stored_input), payload in mock_lookup.items():
                        if stored_tool == tool_name and is_semantically_similar(stored_input, input_norm):
                            variants = payload["mutants"]

                            if run_idx < len(variants) and callable(variants[run_idx]):
                                return format_tool_output(variants[run_idx]())

                            return "Error: Not enough variants"

                    return "Error: unexpected tool input" if mutant_type[run_idx] == "error" else ""
                return mocked

            mocked_tools = []
            for original_tool in self.tools:
                mocked_func = make_mock_func(original_tool.name)
                mocked_tools.append(
                    Tool(
                        name=original_tool.name,
                        func=mocked_func,
                        description=original_tool.description
                    )
                )

            hybrid_tools = []
            delayed_counts_by_key = {}
            for original_tool in self.tools:
                def make_hybrid_func(tool_obj):
                    def hybrid_func(input_str: str):
                        input_norm = normalize(input_str)
                        matched_payload = None

                        for (stored_tool, stored_input), payload in mock_lookup.items():
                            if stored_tool == tool_obj.name and is_semantically_similar(stored_input, input_norm):
                                matched_payload = payload
                                break
                        
                        if mutant_type[run_idx] == "delayed response":
                            delay_key = tool_obj.name
                            current_count = delayed_counts_by_key.get(delay_key, 0) + 1
                            delayed_counts_by_key[delay_key] = current_count

            
                            if current_count <= 2:
                                return ""
                            try:
                                if hasattr(tool_obj, "run"):
                                    return format_tool_output(tool_obj.run(input_str))
                                return format_tool_output(tool_obj.func(input_str))
                            except Exception as e:
                                return f"Error: tool execution failed: {e}"

                        if matched_payload is None:
                            try:
                                if hasattr(tool_obj, "run"):
                                    return format_tool_output(tool_obj.run(input_str))
                                return format_tool_output(tool_obj.func(input_str))
                            except Exception as e:
                                return f"Error: {e}"

                        original_obs = matched_payload["original"]
                        variants = matched_payload["mutants"]

                        if mutant_type[run_idx] == 'real/simulated':
                            # First call for this tool is always real
                            if not first_real_by_tool.get(tool_obj.name, False):
                                first_real_by_tool[tool_obj.name] = True
                                try:
                                    if hasattr(tool_obj, "run"):
                                        return format_tool_output(tool_obj.run(input_str))
                                    return format_tool_output(tool_obj.func(input_str))
                                except Exception as e:
                                    return f"Error: {e}"

                            # After the first call for this tool, use probabilistic real/simulated behavior
                            use_real = self.rng.random() < self.real_prob

                            if use_real:
                                try:
                                    if hasattr(tool_obj, "run"):
                                        return format_tool_output(tool_obj.run(input_str))
                                    return format_tool_output(tool_obj.func(input_str))
                                except Exception as e:
                                    return f"Error: {e}"
                            
                            selected_variants = [variants[0], variants[1], variants[2]]
                            valid_variants = [v for v in selected_variants if callable(v)]
                            if valid_variants:
                                chosen = self.rng.choice(valid_variants)
                                return format_tool_output(chosen())

                           
                            return ""

                        return ""

                    return hybrid_func

                hybrid_tools.append(
                    Tool(
                        name=original_tool.name,
                        func=make_hybrid_func(original_tool),
                        description=original_tool.description
                    )
                )

            if isinstance(self.agent, AgentExecutor):
                mocked_executor = AgentExecutor.from_agent_and_tools(
                    agent=self.agent.agent,
                    tools=mocked_tools,
                    verbose=True,
                    handle_parsing_errors=True,
                    return_intermediate_steps=True,
                    max_iterations=10
                )

                hybrid_executor = AgentExecutor.from_agent_and_tools(
                    agent=self.agent.agent,
                    tools=hybrid_tools,
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

                hybrid_executor = AgentExecutor.from_agent_and_tools(
                    agent=self.agent,
                    tools=hybrid_tools,
                    verbose=True,
                    handle_parsing_errors=True,
                    return_intermediate_steps=True,
                    max_iterations=10
                )
            else:
                print("Unsupported agent type.")
                continue

            try:
                
                if mutant_type[run_idx] in {'delayed response','real/simulated'}:
                    mock_response = hybrid_executor.invoke(input={"input": user_input})
                else:
                    mock_response = mocked_executor.invoke(input={"input": user_input})

                mock_intermediate_steps = mock_response.get("intermediate_steps", [])

                abstractor = AgentTraceAbstractor()
                abstractor.process_intermediate_steps(mock_intermediate_steps, mutant_type[run_idx])
                mock_abstract_trace = abstractor.get_abstract_trace()

                trace_analyzer = TraceAnalyzer(
                    user_input=user_input,
                    final_answer=str(mock_response.get("output", "")),
                    tools=self.tools,
                    mode='mock', mutant_type=mutant_type
                )

                trajectory = AgentTrajectory()
                trajectory.get_trajetory(
                    user_input,
                    1,
                    input_num,
                    mock_intermediate_steps,
                    mock_response.get("output", "")
                )

                analysis_messages = trace_analyzer.analyze_trace(mock_abstract_trace)
                print(f"Analysis [Mock {run_idx + 1}]:", analysis_messages)

                for msg in analysis_messages:
                    self.global_error_counter[((mutant_type[run_idx],), msg)] += 1

            except Exception as e:
                print(f"Error in mock run {run_idx + 1}: {e}")
                self.global_error_counter[((mutant_type[run_idx],), "Tool Crash")] += 1

        print("\n=== Overall Error Summary Across All Mock Runs ===")
        for (mutant_name, error_msg), count in self.global_error_counter.items():
            print(f"- [Mutant Type: {', '.join(mutant_name)}] {error_msg}: {count} time(s)")

        return self.global_error_counter