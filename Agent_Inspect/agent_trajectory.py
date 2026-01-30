import json
class AgentTrajectory():
    counter = 0
    def __init__(self):
      pass

    def get_trajetory(self,user_input,run_type,input_num,intermediate_steps,final_answer):
        if run_type == 1:
          AgentTrajectory.counter +=1
        messages = [{"role": "user", "content": user_input}]
            
        for action, observation in intermediate_steps:
                tool_input = action.tool_input
                if not isinstance(tool_input, dict):
                    tool_input = {"input": tool_input}
                tool_call_msg = {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": action.tool,
                                "arguments":  json.dumps(tool_input),
                            }
                        }
                    ],
                }
                messages.append(tool_call_msg)

                messages.append({
                    "role": "tool",
                    "content": observation,
                  
                })
        messages.append({
                "role": "assistant",
                "content": final_answer
            })
        if run_type == 0:
            formatted_trace = "output_"+ str(input_num)+ " = " + json.dumps(messages, indent=4)
            filename = "./agent_traj_baseline.txt"
        elif run_type == 1:
            formatted_trace = "output_"+ str(input_num)+ "_mock_" + str(AgentTrajectory.counter) + " = " + json.dumps(messages, indent=4)
            filename = "./agent_traj_sim.txt"

        with open(filename, "a") as f:
            f.write(formatted_trace + "\n\n")
        if AgentTrajectory.counter >= 5:
            AgentTrajectory.counter = 0