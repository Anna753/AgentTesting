from collections import Counter
from collections import defaultdict
import re
from original_run import OriginalRun
from mock_run import MockRun

class AgentInspect():
    def __init__(self):
      pass
    def run(self,agent_executor, tools,input_file_path):
        final_error_counter = Counter()
        final_original_error_counter = Counter()
        with open(input_file_path, "r") as f:
            test_inputs = [line.strip() for line in f if line.strip()]
        results = []
        total_count = 0

        for idx, user_input in enumerate(test_inputs):
            try:
                print(f"\nRunning test {idx+1}: {user_input}")

                original_runner = OriginalRun(agent_executor, tools)
                answer,trace, original_result,count = original_runner.run(user_input,idx+1)
                total_count += count
                for error_msg, count in original_result.items():
                        final_original_error_counter[error_msg] += count
                mock_runner = MockRun(agent_executor, tools)
                mock_result = mock_runner.run(user_input,answer,trace,idx+1)
                final_error_counter.update(mock_result)

            except Exception as e:
                print(f"Skipping input {idx+1} due to error: {e}")
                results.append({"input": user_input, "output": None, "error": str(e)})


        grouped_by_mutant = defaultdict(list)
        with open('./agent_inspect_results_baseline.txt', "w") as f:
          print("\n=== Final Summary grouped by Error Type (Original Run) ===")
          f.write("\n=== Final Summary grouped by Error Type (Original Run) ===\n")
          for error_msg, count in final_original_error_counter.most_common():
              print(f"- {error_msg}: {count} time(s)")
              line = f"- {error_msg}: {count} time(s)\n"
              f.write(line)            
              print(line, end="")    
         
          print("Total failure count",total_count)
          total_line = f"Total failure count: {total_count}\n"
          f.write(total_line)
        grouped_by_mutant = defaultdict(Counter)

        for (mutant_type_tuple, error_msg), count in final_error_counter.items():
            mt = mutant_type_tuple[0]
            grouped_by_mutant[mt][error_msg] += count

        def get_error_number(msg):
            match = re.match(r"Reasoning Error (\d+):", msg)
            return int(match.group(1)) if match else float("inf")  #
        
        with open('./agent_inspect_results_sim.txt', "w") as f:
          print("\n=== Final Error Summary Across All Mock Runs ===")
          f.write("\n=== Final Error Summary Across All Mock Runs ===\n")
          for mutant_type, errors in grouped_by_mutant.items():
              print(f"\n[Mutant Type: {mutant_type}]")
              header = f"\n[Mutant Type: {mutant_type}]\n"
              f.write(header)
              for error_msg, count in errors.items():
                  print(f" {error_msg}' — occurred {count} time(s)")
                  line = f" {error_msg} — occurred {count} time(s)\n"
                  f.write(line)