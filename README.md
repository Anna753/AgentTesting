# Overview
This repository contains source code of AgentInspect, benchmark used for empirical evaluation, and results of different RQs.

```
├── Ablation                               # Details of Ablation Study   
├── Agent_Inspect                          # Source code of AgentInspect
    ├── readme.txt                         # Intructions for using AgentInspect 
    └── requirements.txt                   # Dependency and Python virutal environment information
├── Agents                                 # Contains the test inputs used for evaluating each agent and the results from different
approaches
├── Agent_Inspect_Misalignment             # Source code of extending AgentInspect for other failure modes
├── Labeling                               # Contains final labels used for evaluation and detailed agreement statistics
├── Results                                # Contains the results of different RQs
├── 35_Agents.txt                          # Contains the GitHub link for 35 agents in our benchmark
```
# Ablation
The details of the ablation study is provided in [Ablation](https://github.com/Anna753/AgentTesting/tree/main/Ablation).

# Agent_Inspect
To run AgentInspect, one needs to create a virtual environment. The instructions for creating virtual environment and how to use AgentInspect are provided in [readme.txt](Agent_Inspect/readme.txt). Follow the instructions to reproduce the results.

# Agent_Inspect_Misalignment
The implementation for extending the approach for semantic level failures is available in [Agent_Inspect_Misalignment]([Agent_Inspect/readme.txt](https://github.com/Anna753/AgentTesting/tree/main/Agent_Inspect_Misalignment)). 

# Agents
The detailed description of the test inputs used to evaluate each agent along with the results obtained from different approaches is provided in [Agents](Agents).

# Labeling
The detailed agreement statistics during manual labeling and the labels obtained after agreement for both baseline and simulated settings are provided in [Labeling](Labeling).

# Results
The detailed results for 35 agents in our benchmark for each RQs in the paper are provided in [Results](Results).

# Benchmark
The GitHub links for 35 agents in our benchmark is provided in [35_Agents](35_Agents.xlsx). We will release the trajectory benchmark upon acceptance of the paper.
