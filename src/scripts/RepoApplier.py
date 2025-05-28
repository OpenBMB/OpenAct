import json
import pickle
import platform
import re
import traceback
from datetime import datetime

import docker
from rich.console import Console
from rich.markdown import Markdown

from  Cacher import cache
from  Creator import Creator
from  functions.functions_action import functions
from  logger import logger
from  Modifier import Modifier
from  utils import (calculate_file_count, dockerwrite,
                           dockerwrite_empty_file, download,
                           explore_container_directory, gpt4, gpt4_functions,
                           read_issues, subdir, sys, upload, write_des, write_experience)


class RepoApplier:
    """
    This class applies a GitHub repository to solve a query using LLM actions.
    """
    
    def __init__(
        self, repo_name, repo_owner, container, readme, workdir="/", use_cache=False
    ):
        """
        Initialize the RepoApplier.
        
        Args:
            repo_name (str): The name of the GitHub repository.
            repo_owner (str): The owner of the GitHub repository.
            container (docker.Container): The Docker container to use.
            readme (str): The content of the repository's README file.
            workdir (str, optional): The working directory in the container. Default is "/".
            use_cache (bool, optional): Whether to use cached data. Default is False.
        """
        self.messages = [{"role": "system", "content": self.system_set()}]
        self.modifier = None
        self.container = container
        self.container.start()
        self.readme = readme
        self.repo_name = repo_name
        self.repo_owner = repo_owner
        self.workdir = workdir
        self.last_issue = None
        self.init_query = None
        self.use_cache = use_cache
        logger.log["apply_phase"].append([])
        logger.update("apply_phase", self.messages[-1])

    def system_set(self):
        """
        Set the system prompt.
        
        Return:
            str: The system prompt read from a file.
        """
        with open("prompts/RepoApplierPrompt.txt", "r") as f:
            return f.read()

    def remove_unicode_block_elements(self, text):
        """
        Remove Unicode block elements from the text.
        
        Args:
            text (str): The input text.
            
        Return:    
            str: The cleaned text with Unicode block elements removed.
        """
        regex = r"[\u2580-\u259F]"

        cleaned_text = re.sub(regex, "", text)

        ansi_escape = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")

        return ansi_escape.sub("", cleaned_text)

    def check(self, path):
        """
        Check the content of a file or directory in the container.
        
        Args:
            path (str): The path to the file or directory.
            
        Return:
            str: JSON-formatted content of the file or directory.
        """
        if self.container.exec_run(["test", "-f", path]).exit_code == 0:
            try:
                file_content = self.container.exec_run(["cat", path]).output.decode(
                    "utf-8"
                )
                if len(file_content) > 1000:
                    file_content = file_content[:500] + "\n...\n" + file_content[-500:]
                content = {"Content of this file": "'''" + file_content + "'''"}
            except UnicodeDecodeError:
                try:
                    binary_content = self.container.exec_run(["cat", path]).output
                    if path.endswith(".pkl"):
                        try:
                            data = pickle.loads(binary_content)
                            content = {
                                "Content of this file": "'''" + str(data) + "'''"
                            }
                        except pickle.UnpicklingError:
                            content = {
                                "Error": "File is a binary file and could not be unpickled."
                            }
                    else:
                        content = {
                            "Error": "File is binary and not a known format to parse."
                        }
                except Exception as e:
                    content = {
                        "Error": "An error occurred while reading the file: " + str(e)
                    }
        elif self.container.exec_run(["test", "-d", path]).exit_code == 0:
            file_count = calculate_file_count(self.container, path)
            print(file_count)
            if file_count >= 80:
                content = (
                    "This directory is too large to be shown. Please choose a smaller subdirectory. And the subdirectories of this directory are: "
                    + ", ".join(subdir(self.container, path))
                    + "."
                )
                return json.dumps({"Warning": content})
            else:
                content = {
                    "Content of this directory": "'''"
                    + str(
                        explore_container_directory(self.container, path, file_count)
                    ).replace(": 0", "")
                    + "'''"
                }
        else:
            if self.repo_name in path:
                content = f"This path doesn't exist. Please study relevant bash commands in the readme file carefully and give me your modified path. If you can't locate where the repo is saves, you should check what is under the root directory."
            else:
                content = f"This path doesn't exist. Please study relevant bash commands in the readme file carefully and give me your modified path. Don't forget that the reposiotry's name is '{self.repo_name}'"
            return json.dumps({"Error": content})

        return json.dumps(content)

    def handle_output(self, message, messages={}):
        """
        Handle the output of a program execution.
        
        Args:
            message (str): The output message.
            messages (dict, optional): Additional messages. Default is an empty dict.
        
        Return:
            str: JSON-formatted result or error message.
        """
        if messages == {}:
            system_handle_output = f"""You are a professional programmer. You are using a github repository as a tool to solve a query. However, the output of the program is too long and is not suitable to be the answer of original query. Usually, the length excesses because some useful formatted data is contained as natural language in the output, or the verbose part doesn't doesn't include useful information to answer the query.

You will be given the original query and the first and last part of the output. The complete output is saved at '{self.save_dir}' in the container.

If you think the verbose part doesn't include useful information to answer the query, your response should be structured as follows:

Answer: <summary of content of the output>

Eles, if you think the omitted part of the output includes important information, your task is to write a python program to handle the complete output and save necessary data in a more formatted data structure (like .csv) in another file. Note that the directory the new file will be saved in may not exist, so you should use `os.makedirs` to make sure the target directory exists. You also need to answer the original query in natural query based on the first and last part of the output (data, if any, needs to be included), which should also contain where you saved the handled information.

Even the original file mainly contains formatted data, they might also include some unformatted information. You can use try-except method to ensure the success of processing of the lines in the output.

The paths in your program shouldn't be virtual, but should be real. The paths in your program should all be absolute paths. You should give me the complete program.

Your response should be structured as follows:

Answer: <natural language answer to the query (path to where you saved the handled data must bu declared here)>
The program is:
\'\'\'
<content of the python file>
\'\'\'
"""
            content = (
                "Query: "
                + self.init_query
                + "\nFirst and last part of the output: \n'''\n"
                + message
                + "\n'''"
            )
            message_mod = [
                {"role": "system", "content": system_handle_output},
                {"role": "user", "content": content},
            ]
            dockerwrite_empty_file(self.container, self.workdir + "data_handler.py")
        else:
            dockerwrite(
                self.workdir + "data_handler.py", "", self.container, self.workdir
            )
            messages.append(
                {
                    "role": "user",
                    "content": "The program report an error: ```\n"
                    + message
                    + "\n```\n\nPlease modify the program and give me the entire modified program.",
                }
            )
            message_mod = messages
        response = gpt4(message_mod)
        message_mod.append({"role": "assistant", "content": response})
        if "The program is:" not in response:
            answer = response[6:].strip()
            return json.dumps({"Result": answer})
        try:
            answer = re.findall(r"Answer: (.+?)The program is", response, re.DOTALL)[
                0
            ].strip()
        except:
            try:
                answer = message.split("```")[0][:-16]
            except:
                answer = message.split("'''")[0][:-16]
        try:
            code = re.findall(r"'''.*?\n(.+?)'''", response, re.DOTALL)[0].strip()
        except:
            code = re.findall(r"```.*?\n(.+?)```", response, re.DOTALL)[0].strip()
        dockerwrite(self.workdir + "data_handler.py", code, self.container)
        exit_code, output = self.container.exec_run(
            f"python {self.workdir}data_handler.py"
        )
        output = output.decode("utf-8")
        print(output)
        if exit_code == 0:
            if len(message_mod) > 3:
                return
            return json.dumps(
                {
                    "Result": "Original output is too long to show, and it was saved in `output.txt`. Following is the summary to the output of the program, you should notice the path where the adjusted output is saved. "
                    + answer
                }
            )
        else:
            self.handle_output(message, message_mod)
            return json.dumps({"Result": answer})

    def execute(self, command, type, verbose):
        """
        Execute a command in the container.
        
        Args:
            command (str): The command to execute.
            type (bool): Whether to handle the output as structured data.
            verbose (bool): Whether to include full output in the response.
        
        Return:
            str: JSON-formatted result or error message.
        """
        sys.stdout.print_colored(command, "red")
        exit_code, output = self.container.exec_run(command)
        output = self.remove_unicode_block_elements(output.decode("utf-8"))
        if exit_code == 0 and not verbose:
            return json.dumps(
                {
                    "Output": "Executed successfully. The output of the execution is omitted."
                }
            )
        if self.workdir == "/":
            save_dir = "/output.txt"
        else:
            save_dir = self.workdir + "output.txt"
        print(save_dir)
        dockerwrite_empty_file(self.container, save_dir)
        successfully_written = dockerwrite(
            save_dir, output, self.container, self.workdir
        )
        sys.stdout.print_colored(output, "cyan")

        system_exe = """You are a professional programmer. You will be given a query and the output of a program and judge whether the output contains what the query asks for. If so, you should convert the output to natural language that answers the query. If not, you should tell me the problem with the output.

        If the output is too long, then you will only be given the first and last part of the output, which is abundant for your judgement because the output is usually in a structured format. If the output contains requires messages and is just cut off, your judge should be "Yes".If required details don't seem to be contained in the output, your judge should be "No". If the message is cut off but not contains required message, like the message is just log of download, which is not what the query requires, your judge should be "No". 

        Your response should be structured as follows:
        Judge: Yes/No
        Message: <(if Judge is Yes)modified output in natural language which contains what the query asks for>/<(if Judge is No)problem with the output>
        """
        if len(output) > 8000:
            output_for_gpt4 = output[:4000] + "\n...\n" + output[-4000:]
        else:
            output_for_gpt4 = output

        if exit_code != 0:
            return json.dumps({"Error": output_for_gpt4})
        elif len(output) <= 500:
            return json.dumps({"Result": output_for_gpt4})

        content = (
            "Query: "
            + self.init_query
            + "\nOutput of the program: \n'''\n"
            + output_for_gpt4
            + "\n'''"
        )
        message_exe = [
            {"role": "system", "content": system_exe},
            {"role": "user", "content": content},
        ]
        if type and len(output) > 16000 and successfully_written:
            return self.handle_output(output_for_gpt4)
        else:
            return json.dumps({"Output": output_for_gpt4})

    def call_func(self, func_name, func_para):
        """
        Call a specific function with the given parameters.
        
        Args:
            func_name (str): The name of the function to call.
            func_para (dict): The parameters for the function.
            
        Return:
            str: JSON-formatted result or error message.
        """
        try:
            if func_name == "check_file_or_directory":
                path = func_para["target_path"]
                return self.check(path)
            elif func_name == "modify_file_content":
                path = func_para["target_path"]
                query = func_para["modification_query"]
                issue_derived = func_para["issue_derived"]
                if (
                    "continuePreviousProcess" in func_para
                    and func_para["continuePreviousProcess"] == True
                ):
                    modifier = self.modifier
                    modifier.messages.append(
                        {
                            "role": "function",
                            "name": "submit",
                            "content": json.dumps(
                                {
                                    "Feedback": func_para["thought"]
                                    + func_para["modification_query"]
                                }
                            ),
                        }
                    )
                else:
                    self.modifier = modifier = Modifier(
                        self.container, self.repo_name, workdir=self.workdir
                    )
                if issue_derived:
                    return modifier.modifier(query, path, self.last_issue)
                else:
                    return modifier.modifier(query, path)
            elif func_name == "write_a_file":
                file_path = func_para["file_path"]
                requirements = func_para["requirements"]
                creator = Creator(self.container, self.repo_name, self.workdir)
                if "path_of_file_to_refer_to" in func_para:
                    path_of_the_file_to_imitate = func_para["path_of_file_to_refer_to"]
                    return creator.direct_create(
                        requirements, file_path, path_of_the_file_to_imitate
                    )
                else:
                    return creator.direct_create(requirements, file_path)
            elif func_name == "execute_command":
                if "type" in func_para:
                    type = func_para["type"]
                else:
                    type = False
                if "verbose" in func_para:
                    verbose = func_para["verbose"]
                else:
                    verbose = False
                command = func_para["command"]
                return self.execute(command, type, verbose)
            elif func_name == "upload_directory_to_container":
                local_path = func_para["local_path"]
                container_path = func_para["container_path"]
                return upload(self.container, local_path, container_path)
            elif func_name == "download_directory_from_container":
                local_path = func_para["local_path"]
                container_path = func_para["container_path"]
                return download(self.container, container_path, local_path)
            elif func_name == "read_issues_to_solve_problem":
                query = func_para["query"]
                self.last_issue = read_issues(
                    query, self.repo_owner, self.repo_name, self.init_query
                )
                issue = json.loads(self.last_issue)
                if "Issue" not in issue:
                    return self.last_issue
                issue_content = issue["Issue"]
                hint = issue["Hint"]
                if len(issue_content) > 600:
                    issue_content = issue_content[:300] + "..." + issue_content[-300:]
                return json.dumps({"Issue": issue_content, "Hint": hint})
        except Exception as e:
            if str(e) == "":
                e = "Command execution timeout"
            traceback.print_exc()
            print(traceback.format_exc())
            return json.dumps({"error": f"Error happens :{str(e)}."})

    def func_chain(self, funcs, func_name, back_content):
        """
        Chain function calls based on the assistant's response.
        
        Args:
            funcs (list): The list of available functions.
            func_name (str): The name of the current function.
            back_content (str): The content returned from the previous function.
            
        Return:  
            str: The final result of the function chain.
        """
        while True:
            self.messages.append(
                {"role": "function", "name": func_name, "content": back_content}
            )
            logger.update("apply_phase", self.messages[-1])
            func_call = gpt4_functions(self.messages, funcs)
            self.messages.append(
                {"role": "assistant", "content": None, "function_call": func_call}
            )
            logger.update("apply_phase", self.messages[-1])
            func_name = func_call["name"]
            func_para = json.loads(func_call["arguments"])
            if func_name == "submit":
                write_des(self.readme, self.repo_name)
                write_experience(self.repo_name, self.init_query, self.messages)
                return func_para["result"]
            back_content = self.call_func(func_name, func_para)
            sys.stdout.print_colored(back_content, "blue")

    def start_chain(self, funcs):
        """
        Start the function chain by sending the initial prompt.
        
        Args:
            funcs (list): The list of available functions.
            
        Return:
            str: The final result of the function chain.
        """
        console = Console()
        console.print(Markdown(self.readme))
        content = (
            "Request: "
            + self.init_query
            + "\nReadme of the repository: \n'''\n"
            + self.readme
            + "\n'''"
        )
        self.messages[0]["content"] = self.messages[0]["content"].replace(
            "<==repo_name==>", self.repo_name
        )
        if self.data_path:
            self.messages[0]["content"] = self.messages[0]["content"].replace(
                "<==data_path==>", self.data_path
            )
        else:
            self.messages[0]["content"] = self.messages[0]["content"].replace(
                "<==data_path==>", ""
            )
        # print(cache[self.repo_name].keys())
        if (
            self.use_cache
            and self.repo_name in cache
            and "experience" in cache[self.repo_name]
        ):
            print(1154514)
            content += f"Experience of applying that you can refer to: {cache[self.repo_name]['experience']}."

        self.messages.append({"role": "user", "content": content})
        logger.update("apply_phase", self.messages[-1])
        func_call = gpt4_functions(self.messages, funcs)
        self.messages.append(
            {"role": "assistant", "content": None, "function_call": func_call}
        )
        logger.update("apply_phase", self.messages[-1])
        func_name = func_call["name"]
        func_para = json.loads(func_call["arguments"])
        back_content = self.call_func(func_name, func_para)
        sys.stdout.print_colored(back_content, "blue")
        return self.func_chain(funcs, func_name, back_content)

    def generate_actions(self, query, messages=[], data_path=None):
        """
        Generate LLM actions to solve the given query.
        
        Args:
            query (str): The query to solve.
            messages (list, optional): The list of previous messages. Default is an empty list.
            data_path (str, optional): The path to the data directory. Default is None.
            
        Return:
            tuple: A tuple containing the final result and the list of messages.
        """
        self.data_path = data_path
        self.init_query = query
        if len(messages) > 1:
            self.messages = messages
            return (
                self.func_chain(functions, "submit", messages[-1]["content"]),
                self.messages,
            )
        return self.start_chain(functions), self.messages

    def save_messages(self):
        """
        Save the messages to a file with a timestamped filename.
        """
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"log_files/messages_{current_time}.pkl"
        with open(filename, "wb") as file:
            pickle.dump(self.messages, file)

        print(f"Messages saved to {filename}")