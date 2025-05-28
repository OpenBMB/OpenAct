import re

from  Cacher import cache, save_cache
from  utils.OpenaiAPI import gpt4, handle_readme


def generate_des(readme):
    system = """You are a professional programmer. You have just used a github repository as a tool to fulfill a task, you want to write a description of the repository to other programmers. Your description should contain nothing but all its functions (works that can be done with this repository). Your description should be precise. You will be given the readme of the repository.
    
Your answer should be formatted ans follow:

Description: <your description>
"""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": readme},
    ]
    response = gpt4(messages)
    description = re.findall(r"Description:(.+)", response, re.DOTALL)[0].strip()
    return description


def write_des(readme, repo_name):
    if "description" not in cache[repo_name]:
        des = generate_des(handle_readme(readme))
        cache[repo_name]["description"] = des
        save_cache(cache)
