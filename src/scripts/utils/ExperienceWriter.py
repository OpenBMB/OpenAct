import json

from  Cacher import cache, save_cache
from  utils.OpenaiAPI import gpt4

sys_exp = """You are a professional programmer. You have successfully used a github repository as a tool to solve a query and you want to write your experience of using this repository to other programmers. 

You don't need to mention the result of any query, just analyse the process and tell the next user how to avoid unnecessary tries and how to use the repository efficiently, especially significant functions to call and commands to execute. You should identify and eliminate unnecesary actions in the history. Your answer should be formatted like following;

"
A. Query: query/task
1. function name: function parameters
2. function name: function parameters
3. function name: function parameters
......
"

Now you will be given the history of your using this repository. You should write your experience based on the history.
"""

sys_exp_ = """You are a professional programmer. You have successfully used a github repository as a tool to solve a query and you want to write your experience of using this repository to other programmers. 

You don't need to mention the result of any query, just analyse the process and tell the next user how to avoid unnecessary tries and how to use the repository efficiently, especially significant functions to call and commands to execute. You should identify and eliminate unnecesary actions in the history. Your answer should be formatted like following;

"
A. Query: query/task (existed)
1. function name: function parameters
2. function name: function parameters
3. function name: function parameters
......

B. Query: query/task (your job)
1. function name: function parameters
2. function name: function parameters
3. function name: function parameters
......
"

Now you will be given the history of your using this repository and an existing experience document. You should write a better document based on them. Note that the tasks completed in the document might be different from the task you have achieved, so you should maintain what the document has had and add what you summarize. If the same query have already exists, you don't need to add it again. Write the complete experience.

"""


def write_experience(repo_name, query, messages):
    if "experience" in cache[repo_name]:
        experience = cache[repo_name]["experience"]
    else:
        experience = None
    focused_messages = []
    for message in messages:
        if message["role"] == "user":
            focused_messages.append(f"Query: {query}")
        elif message["role"] == "assistant":
            func_name = message["function_call"]["name"]
            func_para = message["function_call"]["arguments"]
            focused_messages.append(
                f"Function Call: {func_name}, Arguments: {func_para}"
            )
        elif message["role"] == "function":
            focused_messages.append(f'Function Result: {message["content"]}')
    focused_messages = "\n".join(focused_messages)
    if experience is not None:
        messages = [
            {"role": "system", "content": sys_exp_},
            {
                "role": "user",
                "content": "Existing Experience: "
                + experience
                + "\n\nThis process: "
                + focused_messages,
            },
        ]
    else:
        messages = [
            {"role": "system", "content": sys_exp},
            {"role": "user", "content": focused_messages},
        ]
    response = gpt4(messages)
    cache[repo_name]["experience"] = response
    save_cache(cache)
