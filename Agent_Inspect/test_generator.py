import ast
from langchain_openai import ChatOpenAI
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import re
import random
import os
import getpass

class TestInputGenerator:
    def __init__(self,llm):
        self.llm = llm
    def generate_tests(self,agent_setup, role, purpose, error_type):

        prompt = f""" You are a test input generator. You are given a LangChain-based agent designed using the ReAct paradigm {agent_setup}.
        The agent has the following role and purpose:
        Role: {role}
        Purpose: {purpose}
       
        Your task is to generate 6 test inputs for this agent which causes tools to generate {error_type}.

        Ensure your test inputs include:

        - Single-tool scenarios – queries that require only one tool to answer.
        - Multi-tool scenarios – queries that require the LLM to invoke multiple tools in a meaningful and logical sequence.
        - Each input must be a **plausible, fact-based, real-world query** — avoid fictional entities, contradictory premises, or impossible requirements.
        - Do not include tool names in test inputs.

        Output:
        - Return  6 test inputs.
        - All test inputs should be unique (not included in {combined_inputs})

        - **Do not** include explanations or markdown only return questions.
        """.strip()
        response = self.llm.invoke(prompt)
        test_inputs = response.content.strip()
        return test_inputs

errors = ["correct response", "error response", "delayed response", "incomplete response", "no response"]
os.environ["OPENAI_API_KEY"] = getpass.getpass("OpenAI Key:\n")
llm = ChatOpenAI(model_name="gpt-4o", temperature=0, verbose=True)
combined_inputs = []
for error_type in errors:
    test_generator = TestInputGenerator(llm)
    test_inputs = test_generator.generate_tests("""
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    tools = load_tools(["serpapi", "llm-math"], llm=llm)

""","Web search and math agent","assist users with answering the questions related to web search and mathematical calculations",error_type)
    test_inputs_list = [re.sub(r"^\d+\.\s*", "", line.strip()).strip('"') for line in test_inputs.split("\n") if line.strip()]
    combined_inputs.extend(test_inputs_list)
all_inputs = []
random.shuffle(combined_inputs)
with open("30_test_inputs.txt", "w") as f:
    for idx, input_text in enumerate(combined_inputs, 1):
        f.write(f"{input_text}\n")