from trace_abstractor import AgentTraceAbstractor
# from sentence_transformers import SentenceTransformer, util
from goal_misalignment_helper import detect_trace_task_misalignment
class GoalMisalignment:
      def __init__(self,user_input):
          self.user_input = user_input.strip()
          self.message = []
          self.premises = {}

      def misalignment(self, trace):
          hypothesis = "This step is relevant to " + self.user_input
          for i, step in enumerate(trace):
                action = str(step.get("Action", "")).strip()
                action_input = str(step.get("Action Input", "")).strip().lower()
                observation = str(step.get("Observation", "")).strip().lower()
                
                self.premises[f"p{i}"] = f"This step gathers information about {action_input}"
         
          result = detect_trace_task_misalignment(
                        query=self.user_input,
                        premises=self.premises,
                        hypothesis=hypothesis,
                        
                    )
          if result["trace_misalignment"]:
                     return 1
          return 0