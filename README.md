# Overview
This repository contains source code of AgentInspect, benchmark used for empirical evaluation, and results of different RQs.

```

├── Agent_Inspect                          # Source code of AgentInspect
    ├── readme.txt                         # Intructions for using AgentInspect 
    └── requirements.txt                   # Dependency and Python virutal environment information
├── Agents                                 # Contains the test inputs used for evaluating each agent and the results from different approaches
├── Labeling                               # Contains final labels used for evaluation and detailed agreement statistics
├── Results                                # Contains the results of different RQs
├── 35_Agents.txt                          # Contains the GitHub link for 35 agents in our benchmark
```

# Agent_Inspect
To run AgentInspect, one needs to create a virtual environment. The instructions for creating virtual environment and how to use AgentInspect are provided in [readme.txt](Agent_Inspect/readme.txt). Follow the instructions to reproduce the results.

# Agents
The detailed description of the test inputs used to evaluate each agent along with the results obtained from different approaches is provided in [Agents](Agents).

# Labeling
The detailed agreement statistics during manual labeling and the lables obtained after agreement for both baseline and simulated settings are provided in [Labeling](Labeling).

# Results
The detailed results for 35 agents in our benchmark for each RQs in the paper are provided in [Results](Results).

# Benchmark
The GitHub links for 35 agents in our benchmark is provided in [35_Agents](35_Agents.xlsx). We will release the trajectory benchmark upon acceptance of the paper.
