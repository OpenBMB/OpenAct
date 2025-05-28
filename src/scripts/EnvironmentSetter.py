import json
import pickle
import re
import traceback

import docker

from  Cacher import cache, save_cache
from  Creator import Creator
from  functions.functions_setup import functions
from  logger import logger
from  Modifier import Modifier
from  utils import (EnhancedContainer, build_and_run_container,
                           calculate_file_count, explore_container_directory,
                           find_lines_with_string, gpt4_functions,
                           handle_readme, read_PRs, subdir, sys)


class RepoSetter:
    """
    This class is responsible for setting up a repository environment by cloning the repository,
    reading the README file, and executing necessary setup steps using an AI-assisted process.
    It also handles caching of the setup environment for future use.
    """
    
    def __init__(self):
        """
        Initialize the RepoSetter instance with default values and configurations.
        """
        self.messages = [{"role": "system", "content": self.system_set()}]
        self.modifier = None
        self.owner = None
        self.repo_name = None
        self.container = None
        self.return_container = None
        self.client = None
        self.data_path = None
        self.work_dir = "/"
        self.repo_url = None
        self.dockerfile = None
        self.entrypoint = None
        self.readme = None
        self.existing_df_used = False
        logger.log["setup_phase"].append([])
        logger.update("setup_log", self.messages[-1])

    def system_set(self):
        """
        Reads the system prompt from a file and returns it as a string.

        Returns:
            str: The system prompt for the AI assistant.
        """
        with open("prompts/RepoSetterPrompt.txt", "r") as f:
            return f.read()

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
            try:
                content = {
                    "Content of this file": "'''"
                    + self.container.exec_run(["cat", path]).output.decode("utf-8")
                    + "'''"
                }
            except UnicodeDecodeError:
                try:
                    binary_content = self.container.exec_run(["cat", path]).output
                    if path.endswith(".pkl"):
                        try:
                            data = pickle.loads(binary_content)
                            if str(data).strip() == "":
                                content = {"Warning": "Binary file not readable."}
                            else:
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
                content = f"This path doesn't exist. Please study relevant bash commands in the readme file carefully and give me your modified path."
            else:
                content = f"This path doesn't exist. Please study relevant bash commands in the readme file carefully and give me your modified path. Don't forget that the reposiotry's name is '{self.repo_name}'"
            return json.dumps({"Error": content})

        return json.dumps(content)

    def call_func(self, func_name, func_para):
        """
        Calls a specific function with the given parameters.

        Args:
            func_name (str): The name of the function to call.
            func_para (dict): The parameters to pass to the function.

        Returns:
            str: JSON-formatted string containing the result of the function call,
                 or an error message if an exception occurs.
        """
        try:
            if func_name == "execute_command":
                command = func_para["command"]
                if "verbose" in func_para:
                    verbose = func_para["verbose"]
                else:
                    verbose = False
                if "conda create" in command:
                    return json.dumps(
                        {"warning": "You should not create a new environment."}
                    )
                if "1min" in command:
                    return json.dumps(
                        {
                            "result": "Executed successfully. The output of the execution is omitted."
                        }
                    )
                print(command)
                exit_code, output = self.container.exec_run(command)
                if exit_code != 0:
                    exit_code, output = self.container.exec_run(command)
                output = output.decode("utf-8")
                if exit_code == 0 and not verbose:
                    return json.dumps(
                        {
                            "Output": "Executed successfully. The output of the execution is omitted."
                        }
                    )
                print(output)
                if len(output) < 100:
                    return json.dumps({"output": output})
                if exit_code == 0 and "ls" not in command:
                    output = (
                        "Executed successfully. The output of the execution is omitted."
                    )
                if len(str(output)) > 2000:
                    output = output[:1000] + "..." + output[-1000:]
                if "No module named" in output:
                    return json.dumps(
                        {
                            "output": output,
                            "Hint": "You should check whether you have done required steps to set up the environment in the readme.",
                        }
                    )
                return json.dumps({"output": output})
            elif func_name == "read_pulls_to_solve_problem":
                problem = func_para["query"]
                return read_PRs(self.container, problem, self.owner, self.repo_name)
            elif func_name == "modify_file_content":
                path = func_para["target_path"]
                query = func_para["modification_query"]
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
                    self.modifier = modifier = Modifier(self.container, self.repo_name)
                return modifier.modifier(query, path)
            elif func_name == "write_a_file":
                file_path = func_para["file_path"]
                requirements = func_para["requirements"]
                creator = Creator(self.container, self.repo_name, self.work_dir)
                if "path_of_file_to_refer_to" in func_para:
                    path_of_the_file_to_imitate = func_para["path_of_file_to_refer_to"]
                    return creator.direct_create(
                        requirements, file_path, path_of_the_file_to_imitate
                    )
                else:
                    return creator.direct_create(requirements, file_path)
            elif func_name == "set_container_with_existed_dockerfile":
                try:
                    path = func_para["path"]
                except KeyError:
                    return json.dumps(
                        {"warning": "You should offer the path of the dockerfile"}
                    )
                (
                    self.return_container,
                    message,
                    self.dockerfile,
                ) = build_and_run_container(self.container, path, self.repo_url)
                self.entrypoint = find_lines_with_string(self.dockerfile, "ENTRYPOINT")
                self.existing_df_used = True
                print(self.entrypoint)
                return message
            if func_name == "check_file_or_directory":
                path = func_para["target_path"]
                return self.check(path)
        except Exception as e:
            print(traceback.format_exc())
            if str(e) == "":
                e = "Command execution timeout"
            return json.dumps({"error": f"Error happens :{str(e)}."})

    def func_chain(self, funcs, func_name, back_content):
        """
        Executes a chain of functions based on the AI assistant's responses.

        Args:
            funcs (list): The list of available functions.
            func_name (str): The name of the current function.
            back_content (str): The content returned by the previous function.

        Returns:
            str: A message indicating the completion of the environment setup and data preparation.
        """
        while True:
            self.messages.append(
                {"role": "function", "name": func_name, "content": back_content}
            )
            logger.update("setup_log", self.messages[-1])
            func_call = gpt4_functions(self.messages, funcs)
            self.messages.append(
                {"role": "assistant", "content": None, "function_call": func_call}
            )
            logger.update("setup_log", self.messages[-1])
            func_name = func_call["name"]
            func_para = json.loads(func_call["arguments"])
            if func_name == "submit":
                if "path_to_report" in func_para:
                    self.data_path = func_para["path_to_report"]
                if "work_directory" in func_para:
                    self.work_dir = func_para["work_directory"]
                return "Environment has been set and data has been prepared."
            back_content = self.call_func(func_name, func_para)
            sys.stdout.print_colored(back_content, "blue")

    def start_chain(self, funcs):
        """
        Starts the function chain by processing the README and executing the first function.

        Args:
            funcs (list): The list of available functions.

        Returns:
            str: A message indicating the completion of the environment setup and data preparation.
        """
        self.messages[0]["content"] = self.messages[0]["content"].replace(
            "<==repo_name==>", self.repo_name
        )
        self.messages.append({"role": "user", "content": self.readme})
        logger.update("setup_log", self.messages[-1])
        func_call = gpt4_functions(self.messages, funcs)
        self.messages.append(
            {"role": "assistant", "content": None, "function_call": func_call}
        )
        logger.update("setup_log", self.messages[-1])
        func_name = func_call["name"]
        func_para = json.loads(func_call["arguments"])
        back_content = self.call_func(func_name, func_para)
        sys.stdout.print_colored(back_content, "blue")
        return self.func_chain(funcs, func_name, back_content)

    def check_image_exists(self, image_name):
        """
        Checks if a Docker image with the given name exists.

        Args:
            image_name (str): The name of the Docker image to check.

        Returns:
            bool: True if the image exists, False otherwise.
        """
        client = docker.from_env()
        images = client.images.list()
        for image in images:
            if image_name in [tag.split(":")[0] for tag in image.tags]:
                return True
        return False

    def set_repo(self, repo_url, use_cache=True):
        """
        Sets up the repository environment by cloning the repository, reading the README file,
        and executing necessary setup steps using an AI-assisted process. It also handles
        caching of the setup environment for future use.

        Args:
            repo_url (str): The URL of the repository to set up.
            use_cache (bool, optional): Whether to use cached setup if available. Defaults to True.

        Returns:
            tuple: A tuple containing the repository name, setup result message, container object,
                   owner, data path, working directory, README content, and entrypoint.
        """
        self.repo_url = repo_url
        client = docker.from_env()
        match = re.match(r"https:\/\/github\.com\/(.+?)\/(.+?)\.git", repo_url)

        if match:
            self.owner, self.repo_name = match.groups()

        if (
            self.repo_name in cache
            and use_cache
            and self.check_image_exists(f"{self.repo_name.lower()}_image")
        ):
            print("Using cached image.")
            new_container = client.containers.create(
                f"{self.repo_name.lower()}_image",
                tty=True,
                stdin_open=True,
                command="/bin/sh",
                network_mode="host",
            )
            self.container = EnhancedContainer(new_container, client)
            self.container.start()
            self.readme = cache[self.repo_name]["readme"]
            if "entrypoint" in cache[self.repo_name]:
                self.entrypoint = cache[self.repo_name]["entrypoint"]
            if "data_path" in cache[self.repo_name]:
                self.data_path = cache[self.repo_name]["data_path"]
            if "work_dir" in cache[self.repo_name]:
                self.work_dir = cache[self.repo_name]["work_dir"]
            return (
                self.repo_name,
                "Environment has been set and data has been prepared.",
                self.container,
                self.owner,
                self.data_path,
                self.work_dir,
                self.readme,
                self.entrypoint,
            )

        self.container = client.containers.create(
            "condaimage",
            tty=True,
            stdin_open=True,
            command="/bin/sh",
            network_mode="host",
        )
        self.container = EnhancedContainer(self.container, client)
        self.container.start()

        exit_code, output = self.container.exec_run(f"git clone {repo_url}")
        print(output.decode("utf-8"))

        exit_code, output = self.container.exec_run(f"cat {self.repo_name}/README.md")
        if exit_code != 0:
            sub_directory = subdir(self.container, self.repo_name)
            for directory in sub_directory:
                if "readme" in directory.lower():
                    exit_code, output = self.container.exec_run(f"cat {directory}")
                    break

        if exit_code != 0:
            self.readme = "Readme is not found, you should use `check_file_or_directory` to check it from the root directory."
        else:
            self.readme = handle_readme(output.decode("utf-8"))

        result = self.start_chain(functions)

        if not self.return_container:
            self.return_container = self.container

        cache[self.repo_name] = {
            "container_id": self.return_container.id,
            "name": self.repo_name,
            "owner": self.owner,
            "url": repo_url,
            "readme": self.readme,
        }

        if self.data_path:
            cache[self.repo_name]["data_path"] = self.data_path
        if self.work_dir and self.existing_df_used:
            cache[self.repo_name]["work_dir"] = self.work_dir
        if self.entrypoint and self.existing_df_used:
            cache[self.repo_name]["entrypoint"] = self.entrypoint

        save_cache(cache)

        while True:
            try:
                image = self.return_container.commit(
                    repository=f"{self.repo_name.lower()}_image"
                )
                break
            except Exception as e:
                print(e)

        self.return_container.stop()
        self.return_container.remove()

        new_container = client.containers.create(
            f"{self.repo_name.lower()}_image",
            tty=True,
            stdin_open=True,
            command="/bin/sh",
            network_mode="host",
        )
        self.return_container = EnhancedContainer(new_container, client)
        self.return_container.start()

        return (
            self.repo_name,
            result,
            self.return_container,
            self.owner,
            self.data_path,
            self.work_dir,
            self.readme,
            self.entrypoint,
        )
