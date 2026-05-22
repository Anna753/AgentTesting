Instructions for using AgentInspect:

The project assumes a Python 3.X is installed in the user system.
Additionally, the project requires several packages which are listed in requirements.txt file. 
Below, we provide a detailed guide on how to set up a virtual environment and install the necessary packages for running the project:

1. Download the project in your system.

2. Open terminal and navigate to a folder named 'Agent_Inspect'.

3. Create a virtual environment. Run on terminal:

python3 -m venv agentinspect

4. Activate the environment.

5. Install required packages:
pip install -r requirements.txt

6. For test input generation:
	-- In test_generator.py, specify the agent you wish to evaluate, along with its designated role and purpose. For reference, an example configuration for Agent 1 from our benchmark is included. 
	-- Use your OpenAI key to execute it.
	-- This step automatically generates 30 test inputs and writes them to a file 30_test_inputs.txt.
	
7. For trajectory capture, tool response simulation and behavioral analysis:
	-- To run the agents from our benchmark, clone the repository and include Agent_Inspect in the working directory.
	-- In the main file include:
		from agent_inspect import AgentInspect
           	inspector = AgentInspect()
		inspector.run(agent_executor,tools,"../30_test_inputs.txt")

	-- Provide the agent, its integrated tools and 30 test inputs and execute it.
	-- AgentInspect will automatically execute the agent in both baseline and simulated setting and will generate the analysis report at the end.
	-- The final report is saved in text files agent_inspect_results_baseline.txt and agent_inspect_results_sim.txt.
	