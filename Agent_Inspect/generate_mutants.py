
import random
import json


class GenerateMocks:
      def __init__(self):
         pass

      def generate_error_response(self):
            error_messages = [
              "Error: Operation timed out.",
              "Error: Resource not found.",
              "PermissionError: Access is denied.",
              "ValueError: Invalid input provided.",
              "RuntimeError: Unexpected system failure.",
              "Error: Service Unavailable",
              "NotImplementedError: Feature not supported",
              "Error 429: Too many requests",
              "Error: Received empty response from tool",
              "SyntaxError: invalid syntax",

            ]
            return random.choice(error_messages)

      def generate_empty_response(self, data):

              if data is None:
                  return None

              elif isinstance(data, dict):
                  return {k: self.generate_empty_response(v) if isinstance(v, (dict, list)) else None for k, v in data.items()}
              elif isinstance(data, list):
                  if all(isinstance(item, dict) for item in data):
                      return [self.generate_empty_response(item) for item in data]
                  else:
                      return []

              elif isinstance(data, str):
                  return ''

              elif isinstance(data, (int, float, complex)):
                  return None

              else:
                  return None

      def generate_incomplete_response(self, data):

            try:
                if isinstance(data, (dict, list)):
                    string = json.dumps(data)
                else:
                    string = str(data)

                cutoff = max(1, len(string) // 4)  # 1/4th truncation
                return string[:cutoff]

            except Exception as e:
                return ""

      
      def generate_mutants(self,seed_observation):

              mutants = []
              mutants.append(self.generate_error_response())
              mutants.append(self.generate_incomplete_response(seed_observation))
              mutants.append(self.generate_empty_response(seed_observation))

              return mutants