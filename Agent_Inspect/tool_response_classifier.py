import json

class ToolResponseClassifier:
    
    error_keywords = {
        "error", "exception", "traceback", "failed", "not found",
        "unavailable", "invalid", "timeout", "missing", "does not exist","not a valid tool","not valid tool","invalid tool"
    }

    no_data_keywords = {
        "", "none", "null", "n/a", "no data", "na", "not available", "undefined","[]"}

    def __init__(self, custom_errors=None, custom_placeholders=None):
        if custom_errors:
            self.error_keywords.update(set(map(str.lower, custom_errors)))
        if custom_placeholders:
            self.no_data_keywords.update(set(map(str.lower, custom_placeholders)))

    def is_informative(self, value):
        if value is None:
            return False
        if isinstance(value, str):
            val = value.strip().lower()
            return val and val not in self.no_data_keywords
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return True

    def has_informative_data(self, response):
        if isinstance(response, dict):
            for k, v in response.items():
                if isinstance(v, (str, list, dict)) and self.has_informative_data(v):
                    return True
            return False
        if isinstance(response, list):
            return any(self.has_informative_data(item) for item in response)
        return self.is_informative(response)

    def contains_error_keywords(self, text):
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.error_keywords)

    def contains_no_data(self,text):
        text_lower = text.strip().lower()
        return text_lower in self.no_data_keywords


    def classify(self, observation,mutant_type):
        
        if mutant_type in ['partial response']:
            return "Error"

        if observation is None:
            return "No Response"

        if hasattr(observation, "return_values"):
            observation = observation.return_values

        if isinstance(observation, (dict, list)):
            informative = self.has_informative_data(observation)
            response_str = json.dumps(observation)

        else:
            response_str = str(observation).strip()
            informative = self.is_informative(response_str)
        if self.contains_error_keywords(response_str):
            return "Error"

        if self.contains_no_data(response_str) or not informative:
            return "No Response"

        return "Complete Response"