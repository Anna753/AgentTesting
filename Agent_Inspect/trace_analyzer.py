from trace_abstractor import AgentTraceAbstractor
from sentence_transformers import SentenceTransformer, util

class TraceAnalyzer:
      def __init__(self,user_input,final_answer,tools,mode):
          self.tools = tools
          self.mode = mode
          self.user_input = user_input.strip()
          self.final_answer = final_answer.strip()
          self.message = []
          self.trace = AgentTraceAbstractor()
          self.model = SentenceTransformer('all-MiniLM-L6-v2')

      def analyze_trace(self, trace):
          invalid_format = []
          action_input_previous = []
          counter = 0
          count = 0
          count_1 = 0
          check_1 = 0
          check_2 = 0
          complete_tool_response = []
          previous_action = []
          previous_action_input = []
          action_list = []

          fallback_keywords = [
                "unable", "not able", "can't", "fail to", "unknown",
                "not sure", "unavailable", "not available", "missing data", "no data", "no information",
                "not found", "does not exist", "error", "exception", "timeout",
                "tool crashed", "API error", "as an AI", "it's unclear", "ambiguous",
            ]

          tool_names = [tool.name for tool in self.tools]
          
          for i, step in enumerate(trace):
              action = step.get("Action").strip()
              action_input = step.get("Action Input").strip().lower()
              tool_response = step.get("Tool Response")
              observation = step.get("Observation").strip().lower()
              complete_tool_response.append(tool_response)
        
              action_list.append(action)

              def is_semantically_similar(action_input, previous_action_input):
                    embeddings = self.model.encode([action_input, previous_action_input], convert_to_tensor=True)
                    input_sim = util.cos_sim(embeddings[0], embeddings[1]).item()
                    return input_sim >= 0.7



              if action_input:
                  if "Complete Response" in complete_tool_response:
                      for prev_action, prev_input in zip(previous_action, previous_action_input):
                          if action.lower() == prev_action.lower() and is_semantically_similar(action_input.lower(), prev_input.lower()):
                              count+=1
                              if count > 1 :
                                    check_1+=1
                  else:
                     for prev_action, prev_input in zip(previous_action, previous_action_input):
                          if action.lower() == prev_action.lower() and is_semantically_similar(action_input.lower(), prev_input.lower()):
                            count_1+=1
                          if count_1 > 1 :
                                check_2+=1

                  if action_input.lower().startswith("invalid format") or action == 'none' or action_input == 'none' :
                        invalid_format.append(i+1)

              previous_action.append(action)
              previous_action_input.append(action_input)

          responses = {"Error", "No Response"}
          error_responses = [resp.strip() for resp in complete_tool_response]
          has_errors = any(resp in responses for resp in error_responses)
          invalid_actions = [action for action in action_list if action not in tool_names]
          check_3 = 0
          if has_errors:
              if self.mode == 'mock':
                pass
              elif self.mode == 'original':
                  self.message.append("Tool Execution Failure")

          if observation is None or "error" in observation:
                      self.message.append("Tool Crash")
             
          if 'agent stopped' not in self.final_answer.lower():
                  final_answer_lower = self.final_answer.lower()
                  if any(kw in final_answer_lower for kw in fallback_keywords):
                      pass
                  elif not any(resp.strip() == "Complete Response" for resp in complete_tool_response):
                      self.message.append("Task Progression Error: Inference without Evidence -- Agent terminated with a final answer (possible hallucination).")
                  if check_1 > 0 or check_2 > 0:
                      self.message.append("Task Progression Error: Repetitive Reasoning -- Agent terminated with a final answer.")

                  if len(invalid_format) > 0:
                      self.message.append("Task Progression Error: Agent failed to follow the expected format -- Terminated with a final answer.")

                  if len(invalid_actions) > 0:
                      self.message.append("Invalid Tool Invocation: Unavailable Tool Call -- Agent terminated with a final answer.")

                  
                  

          if 'agent stopped' in self.final_answer.lower():
                final_answer_lower = self.final_answer.lower()
                if any(kw in final_answer_lower for kw in fallback_keywords):
                      pass
                if not any(resp.strip() == "Complete Response" for resp in complete_tool_response):
                     self.message.append("Task Progression Error: Failure to Handle Malformed/Errorneous Tool Output -- Agent terminated with no final answer.")
               
                if check_2 > 0 or check_1 > 0:
                      self.message.append("Task Progression Error: Repetitive Reasoning -- Agent terminated with no final answer.")
          
                if len(invalid_format) > 0:
                      self.message.append("Task Progression Error: Agent failed to follow the expected format -- Terminate with no final answer.")

                if len(invalid_actions) > 0:
                      self.message.append("Invalid Tool Invocation: Unavailable Tool Call -- Agent terminated with no final answer.")
          unique_errors = list(dict.fromkeys(self.message))

          return unique_errors