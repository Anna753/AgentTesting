# Original Run
from langchain.agents import Tool, AgentExecutor, BaseSingleActionAgent
from trace_abstractor import AgentTraceAbstractor
from trace_analyzer import TraceAnalyzer
from collections import Counter
from agent_trajectory import AgentTrajectory


class OriginalRun():
    def __init__(self, agent, tools):
          self.agent = agent
          self.tools = tools
          self.count = 0
          self.original_error_counter = Counter()
    def run(self,user_input,input_num):
       
        if isinstance(self.agent, AgentExecutor):
            agent_executor = AgentExecutor.from_agent_and_tools(
                agent=self.agent.agent,
                tools=self.agent.tools,
                verbose=True,
                handle_parsing_errors=True,
                return_intermediate_steps=True,
                max_iterations=10,
               
            )
        elif isinstance(self.agent, BaseSingleActionAgent):
            agent_executor = AgentExecutor.from_agent_and_tools(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                return_intermediate_steps=True,
                max_iterations=10,
                
            )
        try:
            response = agent_executor.invoke(input={"input": user_input})
            final_answer = response.get("output")
            intermediate_steps = response.get("intermediate_steps", [])
            abstractor = AgentTraceAbstractor()
            abstractor.process_intermediate_steps(intermediate_steps,'original')
            abstract_trace = abstractor.get_abstract_trace()
            trace_analyzer = TraceAnalyzer(user_input=user_input, final_answer=str(response["output"]),tools=self.tools,mode='original')
            trajectory = AgentTrajectory()
            trajectory.get_trajetory(user_input,0,input_num,intermediate_steps,response["output"])
            analysis_messages = trace_analyzer.analyze_trace(abstract_trace)
            self.original_error_counter.update(str(msg) for msg in analysis_messages)
           
            if len(analysis_messages) > 0:
                self.count = 1

            print(f"Analysis Original Run:", analysis_messages)

        except Exception as e:
        
            print(f"Error during original run analysis: {e}")
            return None, None, self.original_error_counter

        return final_answer, abstract_trace, self.original_error_counter,self.count