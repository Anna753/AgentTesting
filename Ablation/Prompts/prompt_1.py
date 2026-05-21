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
    def generate_tests(self,agent_setup, role, purpose):

       prompt_1 = f""" You are a test input generator. You are given a LangChain-based agent designed using the ReAct paradigm {agent_setup}.
        The agent has the following role and purpose:
        Role: {role}
        Purpose: {purpose}

        Ensure your test inputs include:
        Output:
        - Return  30 test inputs.
        - All test inputs should be unique.
        - Output must be in this format 'meal of the day', 'city', 'restaurant type', 'additional info'
        - **Do not** include explanations or markdown only return questions.
        """.strip()
        response = self.llm.invoke(prompt_1)
        test_inputs = response.content.strip()
        return test_inputs


os.environ["OPENAI_API_KEY"] = getpass.getpass("OpenAI Key:\n")
llm = ChatOpenAI(model_name="gpt-4o", temperature=0, verbose=True)
combined_inputs = []

test_generator = TestInputGenerator(llm)
test_inputs = test_generator.generate_tests("""
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    tools = load_tools(["serpapi", "llm-math"], llm=llm)

""","Web search and math agent","assist users with answering the questions related to web search and mathematical calculations")
test_inputs_list = [re.sub(r"^\d+\.\s*", "", line.strip()).strip('"') for line in test_inputs.split("\n") if line.strip()]
combined_inputs.extend(test_inputs_list)
all_inputs = []
random.shuffle(combined_inputs)
with open("30_test_inputs.txt", "w") as f:
    for idx, input_text in enumerate(combined_inputs, 1):
        f.write(f"{input_text}\n")