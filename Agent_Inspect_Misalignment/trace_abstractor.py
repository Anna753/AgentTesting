
from tool_response_classifier import ToolResponseClassifier

class AgentTraceAbstractor:
    def __init__(self, tool_response_classifier=None):
        self.last_observation = []
        self.last_thought = []
        self.abstract_trace = []
        self.classifier = ToolResponseClassifier()

    def process_intermediate_steps(self, intermediate_steps,mutant_type):
        for i, (action, observation) in enumerate(intermediate_steps):
            thoughts = action.log.split("Action:")[0].strip()
            response_type = self.classifier.classify(observation,mutant_type)
            step = {
                "Action": action.tool,
                "Action Input": action.tool_input,
                "Tool Response": response_type,
                "Observation" : observation
            }

            self.abstract_trace.append(step)

    def get_abstract_trace(self):
        return self.abstract_trace