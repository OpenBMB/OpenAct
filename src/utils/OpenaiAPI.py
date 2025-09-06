import json
import logging
import os
import re
import sys
from datetime import datetime

import openai
from colorama import Fore, init

from  logger import logger

user_config = json.load(open("config.json"))
GITHUB_TOKEN = user_config["GITHUB_TOKEN"]
OPENAI_API_KEY = user_config["OPENAI_API_KEY"]
messages_length = []

init(autoreset=True)


class LoggerAndPrinter:
    COLOR_MAPPING = {
        "red": Fore.RED,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "blue": Fore.BLUE,
        "magenta": Fore.MAGENTA,
        "cyan": Fore.CYAN,
        "white": Fore.WHITE,
        "black": Fore.BLACK,
    }

    def __init__(self, query=None, identifier=""):
        if query and len(query) > 50:
            query = query[:25] + "..." + query[-25:]
        self.terminal = sys.stdout
        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.INFO)
        log_dir = "last_exp"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = (
            os.path.join(log_dir, f"{timestamp}_{identifier}_{query}.log")
            if query
            else os.path.join(log_dir, f"my_log_{timestamp}_{identifier}.log")
        )

        fh = logging.FileHandler(log_filename)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        fh.setFormatter(formatter)
        self.log.addHandler(fh)

    def write(self, message, color=None):
        if color and color in self.COLOR_MAPPING:
            message = self.COLOR_MAPPING[color] + message
        self.terminal.write(message)
        self.log.info(message.strip("\n"))

    def flush(self):
        self.terminal.flush()

    def print_colored(self, message, color):
        self.write(message + "\n", color)
        self.flush()


sys.stdout = LoggerAndPrinter()

chat_api = 0


def find_lines_with_string(s, string):
    s = str(s)
    lines = s.split("\n")
    matching_lines = [line for line in lines if string in line]
    return "\n".join(matching_lines)


def print_usage():
    print(messages_length)


class GPT:
    def __init__(self, version="gpt-4-1106", temperature=0.7):
        self.version = version
        self.temperature = temperature
        self.accum_len = 0

    def gpt4(self, messages):
        client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            base_url="",
        )

        response = client.chat.completions.create(
            model=self.version,
            messages=messages,
            # max_tokens=2000,
            temperature=self.temperature,
            stop=None,
        )

        messages_length.append(dict(response.usage))
        logger.update("usage", dict(response.usage))
        sys.stdout.print_colored(
            str(response.choices[0].message.content.strip()), "green"
        )

        return response.choices[0].message.content.strip()

    def gpt_summary(self, messages, functions):
        if self.accum_len + len(messages[-1]["content"]) < 12000:
            return self.gpt4_functions(messages, functions)
        else:
            sys_p = """You are a professional programmer. You are using Lange Language Model to manipulate a computer to find and use a github repository to solve a problem. However, now the input to the model, which include former actions, is too long. Your task is to summarize the former process based on the given actions and feedbacks. If there is readme file in the input, you should insure you maintain the key information especially commands and their functions in the file. If there are multiple actions and fedacks, you should summarize what you can learn from it one by one. Also, do not forget the initial query."""
            content = "\n".join(
                [
                    m["content"]
                    if m["content"] is not None
                    else json.dumps(m["function_call"])
                    for m in messages
                ]
            )
            messages_sum = [
                {"role": "system", "content": sys_p},
                {"role": "user", "content": content},
            ]
            response = self.gpt4(messages_sum)
            print(response)
            messages[1:-1] = [{"role": "user", "content": response}]
            return self.gpt4_functions(messages, functions)

    def gpt4_functions(self, messages, functions):
        MAX_TRIES = 5
        tried = 0
        while tried < MAX_TRIES:
            try:
                tried += 1

                client = openai.OpenAI(
                    api_key=OPENAI_API_KEY,
                    base_url="",
                )

                response = None

                response = client.chat.completions.create(
                    model=self.version,
                    messages=messages,
                    tools=functions,
                    temperature=self.temperature,
                    # max_tokens=2000,
                    stop=None,
                )

                messages_length.append(dict(response.usage))
                logger.update("usage", dict(response.usage))
                func_call = response.choices[0]
                func_call = func_call.message.tool_calls
                func_call = func_call[0].function
                func_name = func_call.name
                func_para = func_call.arguments
                func_call = {"name": func_name, "arguments": func_para}
                json.loads(func_para)

                sys.stdout.print_colored(str(func_call), "yellow")

                self.accum_len = response.usage.total_tokens
                return func_call
            except Exception as e:
                import traceback

                traceback.print_exc()
                print(traceback.format_exc())
                print(e)

                if response:
                    response = dict(response)
                    for k in response.keys():
                        v = response[k]
                        if type(v) != str:
                            response[k] = str(v)
                logger.update(
                    "call_error",
                    {"Error": str(e), "input": messages, "output": response},
                )
                messages[-1][
                    "content"
                ] += "\nYou should use tool call to call a function. If you find you are unable to handle the problem, please submit and end this task."


gpt = GPT()


# def gpt4(messages):
#     return gpt.gpt4(messages)


# def gpt4_functions(messages, functions):
#     return gpt.gpt4_functions(messages, functions)


def gpt_summary(messages, functions):
    return gpt.gpt_summary(messages, functions)


def handle_readme(text):
    for _ in range(5):
        text = re.sub(r"<!-.*?->", "", text, flags=re.DOTALL)
        text = re.sub(r"<table>.*?</table>", "", text, flags=re.DOTALL)
        text = re.sub(r"<p.*?>.*?</p>", "", text, flags=re.DOTALL)
        text = re.sub(r"<div.*?>.*?</div>", "", text, flags=re.DOTALL)
        text = re.sub(r"<a.*?>.*?</a>", "", text, flags=re.DOTALL)
        if len(text) > 12000:
            text = re.sub(r"\[(.*?)\]\([^)]*\)", r"\1", text)
            text = re.sub(r"\[(.*?)\]\([^)]*\)", r"\1", text)
    return text

def codellama(text):
    return text

def gpt4(messages):
    message_text = "<s>"
    for message in messages:
        if message["role"] == "system":
            message_text += f"System: {message['content'].replace("\n","")}\n"
        else:
            message_text += f"{message['role']}: {message['content']}\n"
    back_content = codellama(message_text)
    print(back_content)
    return back_content

def gpt4_functions(messages, functions):
    messages = handle_sys_prompt(messages)
    message_text = "<s>"
    for message in messages:
        if message["role"] == "system":
            message_text += f"System: {message['content'].replace("\n","")}\n"
        else:
            message_text += f"{message['role']}: {message['content']}\n"
    message_text += func2text(functions)
    back_content = codellama(message_text)
    print(back_content)
    return text2funccall(back_content)


def func2text(funcs):
    text = ""
    func_index = 0
    for func in funcs:
        func = func["function"]
        text += f"Function {func_index}:\n"
        text += f"Function Name: {func['name']}\n"
        text += f"Function Description: {func['description']}\n"
        for arg in func["parameters"]["properties"]:
            text += f"Argument: {arg['name']}\n"
            text += f"Argument Type: {arg['type']}\n"
            text += f"Argument Description: {arg['description']}\n"
        text += f"Parameters Required: {",".join(func['parameters']['required'])}\n\n\n"
    return text

def handle_sys_prompt(messages):
    str = "You will be provided the functions that you can use to solve the problem.\nYour answer should be a function call with the function name and the arguments.\nYour answer should be in the following format:\n\n{\n\t\"name\": \"function_name\",\n\t\"arguments\": {\n\t\t\"argument1\": \"value1\",\n\t\t\"argument2\": \"value2\",\n\t\t\"argument3\": \"value3\"\n\t}\n}\n\n"
    messages[0]["content"] += str
    return messages

def text2funccall(text):
    text = re.findall(r"{(.+)}", text, re.DOTALL)[0]
    func_call = json.loads(text)
    return func_call