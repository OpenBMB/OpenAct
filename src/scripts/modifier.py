import ast
import json
import platform
import re

import astunparse
import docker

from  functions.functions_modify import functions
from  logger import logger
from  utils import (calculate_file_count, dockerwrite,
                           explore_container_directory, gpt4, gpt4_functions,
                           subdir, sys)


class Modifier:
    """
    This class provides functionality to modify code files based on user queries.
    It interacts with a Docker container to read and write files, and uses AI models
    to generate modifications to the code.
    """
    
    def __init__(self, container, repo_name, issue=None, query_path=None, workdir=None):
        """
        Initializes the Modifier with the given parameters.

        Args:
            container (docker.Container): The Docker container to interact with.
            repo_name (str): The name of the repository.
            issue (str, optional): The issue related to the modification. Defaults to None.
            query_path (str, optional): The path to the query file. Defaults to None.
            workdir (str, optional): The working directory inside the container. Defaults to None.
        """
        with open("prompts/ModifierPrompt.txt", "r") as f:
            self.system = f.read()
        self.messages = [{"role": "system", "content": self.system}]
        self.system_modify = """You are a professional programmer. You will receive a code file and a request to modify a specific function in it. Your task is to give me the modified function.

Please structure your response in the following format:

Thought: <your internal reasoning of making such decision>
Modified Function: 
```python
<the whole function with no omit, there should be no indent before `def`>
```"""
        self.container = container
        self.repo_name = repo_name
        self.workdir = workdir
        self.issue = issue
        self.query_path = query_path
        logger.log["modify_log"].append([])
        logger.update("modify_log", self.messages[-1])

    def check(self, path):
        """
        Checks if a file or directory exists in the container and returns its content.

        Args:
            path (str): The path to the file or directory to check.

        Returns:
            str: JSON-formatted string containing the content of the file or directory,
                 or an error message if the path doesn't exist.
        """
        if self.container.exec_run(["test", "-f", path]).exit_code == 0:
            content = {
                "Content of this file": "'''"
                + self.container.exec_run(["cat", path]).output.decode("utf-8")
                + "'''"
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
                    "Content of this file": "'''"
                    + str(
                        explore_container_directory(self.container, path, file_count)
                    ).replace(": 0", "")
                    + "'''"
                }
        else:
            content = "This path doesn't exist. If you want to check a file, don't forget its suffix."
            return json.dumps({"Error": content})

        return json.dumps(content)

    def replace_function(
        self, original_content, modification_content, class_name, func_name, parameters
    ):
        """
        Replaces a function in the original code with a modified version.

        Args:
            original_content (str): The original code content.
            modification_content (str): The modified function content.
            class_name (str): The name of the class containing the function (if applicable).
            func_name (str): The name of the function to replace.
            parameters (list): The list of parameters of the function.

        Returns:
            str: The updated code content with the replaced function.
        """
        print(modification_content)
        original_ast = ast.parse(original_content)
        modification_ast = ast.parse(modification_content)

        class ReplaceFunctionTransformer(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                if node.name == func_name:
                    if parameters is None or parameters == [
                        arg.arg for arg in node.args.args
                    ]:
                        for mod_node in ast.walk(modification_ast):
                            if (
                                isinstance(mod_node, ast.FunctionDef)
                                and mod_node.name == func_name
                            ):
                                return mod_node
                return node

        if class_name:
            class_transformer = ReplaceFunctionTransformer()

            class ClassVisitor(ast.NodeVisitor):
                def visit_ClassDef(self, node):
                    if node.name == class_name:
                        class_transformer.visit(node)

            ClassVisitor().visit(original_ast)
        else:
            original_ast = ReplaceFunctionTransformer().visit(original_ast)

        return astunparse.unparse(original_ast)

    def modify_entire_file(self, message, path, query_file_path=None):
        """
        Modifies an entire file based on a user query.

        Args:
            message (str): The modification query.
            path (str): The path to the file to modify.
            query_file_path (str, optional): The path to the query file. Defaults to None.

        Returns:
            str: JSON-formatted string indicating the result of the modification.
        """
        exit_code, output = self.container.exec_run(["cat", path])
        if exit_code != 0:
            return json.dumps({"Error": f"{path} file doesn't exist."})

        file = output.decode("utf-8")
        system_mod = """You are a professional programmer. Given a query to modify a file with the original file, you should give me the complete modified file. Don't modify what is not required to modify. Don't modify or add anything to the original file if you have no reason to do so. Only make modification(s) that you are absolutely sure that it will make sense. Notice that format of the modified file should be the same as the original file.

Your response should be structured as follows:
The modified file is:
\'\'\'
<content of the modified file>
\'\'\'
"""

        content = "Query: " + message
        if query_file_path is not None:
            exit_code, query_in_file = self.container.exec_run(["cat", query_file_path])
            if exit_code != 0:
                return json.dumps({"Error": f"File `{query_file_path}` doesn't exist."})
            content = f"Difference of the pull request you should refer to:'''\n{query_in_file.decode('utf-8')}'''"
        if self.issue:
            content += "\nIssue that the query is derived: " + self.issue
        content += "\nOriginal File: \n'''\n" + file + "\n'''"
        message_mod = [
            {"role": "system", "content": system_mod},
            {"role": "user", "content": content},
        ]
        response = gpt4(message_mod)
        try:
            code = re.findall(r"'''(.+?)'''", response, re.DOTALL)[0].strip()
        except:
            code = re.findall(r"```(.+?)```", response, re.DOTALL)[0].strip()
        dockerwrite(path, code, self.container, self.workdir)
        logger.update(
            "modify_detail",
            {
                "query": message,
                "file_path": path,
                "query_file_path": query_file_path,
                "original_code": output,
                "code": code,
            },
        )
        return json.dumps({"Result": "Modification has been made."})

    def modify_function(
        self, query, class_name, func_name, parameters, path, func_message
    ):
        """
        Modifies a specific function in a file based on a user query.

        Args:
            query (str): The modification query.
            class_name (str): The name of the class containing the function (if applicable).
            func_name (str): The name of the function to modify.
            parameters (list): The list of parameters of the function.
            path (str): The path to the file containing the function.
            func_message (str): The message describing the function to modify.

        Returns:
            str: JSON-formatted string indicating the result of the modification.
        """
        exit_code, output = self.container.exec_run(["cat", path])
        if exit_code != 0:
            return json.dumps({"Error": "Such file doesn't exist."})
        file = output.decode("utf-8")
        content = (
            "Request: "
            + query
            + "\nFunction to modify: "
            + func_message
            + "\nOriginal Code:\n```\n"
            + file
            + "\n```"
        )
        messages = [
            {"role": "system", "content": self.system_modify},
            {"role": "user", "content": content},
        ]
        response = gpt4(messages)
        try:
            code = re.findall(r"'''.*?\n(.+?)'''", response, re.DOTALL)[0].strip()
        except:
            code = re.findall(r"```.*?\n(.+?)```", response, re.DOTALL)[0].strip()
        new_file = self.replace_function(file, code, class_name, func_name, parameters)
        print(new_file)
        dockerwrite(path, new_file, self.container, self.workdir)
        return json.dumps({"Result": f"Modification to {func_message} has been made."})

    def call_func(self, query, func_name, func_para):
        """
        Calls a specific function with the given parameters.

        Args:
            query (str): The modification query.
            func_name (str): The name of the function to call.
            func_para (dict): The parameters to pass to the function.

        Returns:
            str: JSON-formatted string containing the result of the function call,
                 or an error message if an exception occurs.
        """
        try:
            if func_name == "check_file_or_directory":
                path = func_para["target_path"]
                return self.check(path)
            elif func_name == "modify_entire_file":
                path = func_para["target_path"]
                query = func_para["modification_query"]
                try:
                    query_file_path = func_para["query_file_path"]
                    if query_file_path not in query:
                        query = f"Apply changes according to {query_file_path}."
                except:
                    query_file_path = None
                return self.modify_entire_file(query, path, query_file_path)
            elif func_name == "modify_a_function":
                path = func_para["target_path"]
                query = func_para["modification_query"]
                func_message = func_name = func_para["function_name"]
                class_name = parameters = None
                if "class_name" in func_para:
                    class_name = func_para["class_name"]
                    func_message = func_para["class_name"] + "." + func_name
                if "parameters" in func_para:
                    parameters = func_para["parameters"]
                    func_message += "(" + ", ".join(func_para["parameters"]) + ")"
                else:
                    func_message += "()"
                return self.modify_function(
                    query, class_name, func_name, parameters, path, func_message
                )
        except Exception as e:
            print(traceback.format_exc())
            return json.dumps({"error": f"Error happens :{str(e)}."})

    def func_chain(self, query, funcs, func_name, back_content):
        """
        Executes a chain of functions based on the AI assistant's responses.

        Args:
            query (str): The modification query.
            funcs (list): The list of available functions.
            func_name (str): The name of the current function.
            back_content (str): The content returned by the previous function.

        Returns:
            str: JSON-formatted string indicating the result of the modification.
        """
        while True:
            self.messages.append(
                {"role": "function", "name": func_name, "content": back_content}
            )
            logger.update("modify_log", self.messages[-1])
            func_call = gpt4_functions(self.messages, funcs)
            self.messages.append(
                {"role": "assistant", "content": None, "function_call": func_call}
            )
            logger.update("modify_log", self.messages[-1])
            func_name = func_call["name"]
            func_para = json.loads(func_call["arguments"])
            if func_name == "submit":
                return json.dumps({"result": "Modification has been made."})
            back_content = self.call_func(query, func_name, func_para)
            sys.stdout.print_colored(back_content, "blue")

    def start_chain(self, query, file, funcs, path):
        """
        Starts the function chain by processing the user query and executing the first function.

        Args:
            query (str): The modification query.
            file (str): The content of the file to modify.
            funcs (list): The list of available functions.
            path (str): The path to the file to modify.

        Returns:
            str: JSON-formatted string indicating the result of the modification.
        """
        print(file)
        if len(self.messages) == 1:
            content = (
                "Request: "
                + json.dumps(query)
                + "\nPath of current file"
                + path
                + "\nContent of the file: \n'''\n"
                + file
                + "\n'''"
            )
            self.messages.append({"role": "user", "content": content})
        logger.update("modify_log", self.messages[-1])
        func_call = gpt4_functions(self.messages, funcs)
        self.messages.append(
            {"role": "assistant", "content": None, "function_call": func_call}
        )
        logger.update("modify_log", self.messages[-1])
        func_name = func_call["name"]
        func_para = json.loads(func_call["arguments"])
        if func_name == "submit":
            return json.dumps({"result": "Modification has been made."})
        back_content = self.call_func(query, func_name, func_para)
        print(back_content)
        return self.func_chain(query, funcs, func_name, back_content)

    def modifier(self, message, path, issue=None):
        """
        Main entry point for code modification.

        Args:
            message (str): The modification query.
            path (str): The path to the file to modify.
            issue (str, optional): The issue related to the modification. Defaults to None.

        Returns:
            str: JSON-formatted string indicating the result of the modification.
        """
        self.issue = issue
        exit_code, output = self.container.exec_run(["cat", path])
        if exit_code != 0:
            return json.dumps({"Error": "Such file doesn't exist."})
        file = output.decode("utf-8")
        if len(file) >= 16000:
            return json.dumps({"Error": "file too long and can't be modified."})
        return self.start_chain(message, file, functions, path)