import argparse
import json
import os
import traceback
from datetime import datetime

import pyfiglet

from  EnvironmentSetter import RepoSetter
from  functions.functions_main import functions
from  logger import logger
from  RepoApplier import RepoApplier
from  RepoSearcher import RepoSearcher
from  utils import (GITHUB_TOKEN, LoggerAndPrinter, gpt, gpt4_functions,
                           print_usage, sys)

MAX_RETRIES = 5


class OpenAgent:
    """
    OpenAgent is a class that uses GitHub repositories to solve a given query.
    It searches for a suitable repository, sets up the environment, and applies the repository code to generate a solution.
    """
    
    def __init__(self, init_query, use_cache=True):
        """
        Initialize the OpenAgent with the given query and cache setting.

        Args:
            init_query (str): The initial query to solve.
            use_cache (bool): Whether to use cached data. Default is True.
        """
        self.use_cache = use_cache
        self.entrypoint = None
        self.container = None
        self.repo_name = None
        self.repo_owner = None
        self.actionmessages = []
        self.init_query = init_query
        self.actiongenerator = None
        self.readme = None
        self.system = """You are a professional programmer. Given a query, your task is to search for a github repository and use it to solve the query.

You should make sure the result of `apply` function well completed the query. If it is lack of required eletemts(like required format in required format), you can call `apply` again if you think the result is close to what you want and you think this repository can be used to solve your query. You can also call `search_by_query` function to find another repository if you think this repository is not suitable for your query.
"""
        self.messages = [{"role": "system", "content": self.system}]
        self.data_path = None
        self.working_dir = "/"
        logger.query = init_query.replace("/", "")
        logger.datetime = datetime.now().strftime("%d-%H-%M-%S")
        logger.update("main_task", self.messages[0])

    # interface to call functions
    def call_func(self, query, func_name, func_para):
        """
        Call the specified function with the given query and parameters.

        Args:
            query (str): The query associated with the function call.
            func_name (str): The name of the function to call.
            func_para (dict): The parameters to pass to the function.

        Returns:
            str: The JSON-encoded result of the function call.
        """
        func_map = {
            "search_by_query": self.search_by_query_func,
            "set_repository": self.set_repository_func,
            "apply": self.apply_func,
        }

        try:
            return func_map[func_name](query, func_para)
        except Exception as e:
            print(traceback.format_exc())
            traceback.print_exc()
            return json.dumps({"error": f"Error happens :{str(e)}."})

    # search a repo to solve the task(in scripts/search.py)
    def search_by_query_func(self, query, func_para):
        """
        Search for a repository to solve the given query.

        Args:
            query (str): The query to search for a repository.
            func_para (dict): Additional parameters for the search function.

        Returns:
            str: The JSON-encoded search result containing the repository name and URL.
        """
        searcher = RepoSearcher(GITHUB_TOKEN)
        repo_name, repo_url = searcher.search_by_query(self.init_query, self.use_cache)
        logger.update("search_result", {"repo_name": repo_name, "repo_url": repo_url})
        return json.dumps({"repo_name": repo_name, "repo_url": repo_url})

    # set repo with search result
    def set_repository_func(self, query, func_para):
        """
        Set the repository based on the search result.

        Args:
            query (str): The query associated with setting the repository.
            func_para (dict): Parameters containing the repository URL.

        Returns:
            str: The JSON-encoded result of setting the repository.
        """
        Setter = RepoSetter()
        (
            self.repo_name,
            result,
            self.container,
            self.repo_owner,
            self.data_path,
            self.working_dir,
            self.readme,
            self.entrypoint,
        ) = Setter.set_repo(func_para["repo_url"], self.use_cache)
        return json.dumps({"result": result})

    # apply through command line tools in docker container
    def apply_func(self, query, func_para):
        """
        Apply the repository code to solve the query.

        Args:
            query (str): The query to solve using the repository code.
            func_para (dict): Additional parameters for applying the repository code.

        Returns:
            str: The JSON-encoded result of applying the repository code.
        """
        if self.working_dir[0] != "/":
            self.working_dir = "/" + self.working_dir
        exit_code, output = self.container.exec_run(f"sh -c 'cd {self.working_dir}'")
        if exit_code != 0:
            self.working_dir = None
        exit_code, output = self.container.exec_run("sh -c 'cd ~ && pwd'")
        output = output.decode("utf-8")
        if not self.working_dir:
            self.working_dir = output.strip()
        if (
            self.actiongenerator
            and "continuePreviousProcess" in func_para
            and func_para["continuePreviousProcess"] == True
        ):
            self.actionmessages.append(
                {
                    "role": "function",
                    "name": "submit",
                    "content": json.dumps(
                        {"Feedback": func_para["thought"] + func_para["query"]}
                    ),
                }
            )
            data_information = ""
        else:
            self.actiongenerator = RepoApplier(
                self.repo_name,
                self.repo_owner,
                self.container,
                self.readme,
                self.working_dir,
                self.use_cache,
            )
            data_information = ""
            if self.working_dir and self.working_dir != "/":
                if not self.working_dir.endswith("/"):
                    self.working_dir += "/"
                data_information += (
                    "\nYou will act at a docker container, and the work directory is: "
                    + self.working_dir
                    + f"It means `cd a` means `cd {self.working_dir}a`. You should pay special attention to this when you execute commands. If in the application pro"
                )
            else:
                data_information += f"The github repository is located at `/{self.repo_name}`. You should pay special attention to this when you execute commands."
            if self.data_path:
                data_information += (
                    "\nHere is some tremendously significant information about data required by the repository that has been downloaded: "
                    + self.data_path
                    + "These data are required by the repository to run successfully. You should pay special attention to its path."
                )
            if self.entrypoint:
                data_information += f"Here is some information of the container's entrypoint. You should refer to it to use the right command: `{self.entrypoint}`."
        back = self.actiongenerator.generate_actions(
            self.init_query + "\n" + func_para["query"] + "\n" + data_information,
            self.actionmessages,
            self.data_path,
        )
        result, self.actionmessages = back
        return json.dumps({"result": result})

    # start main task
    def start_chain(self, query, funcs):
        """
        Start the main task chain to solve the query.

        Args:
            query (str): The query to solve.
            funcs (list): The list of available functions.

        Returns:
            str: The final result of solving the query.
        """
        content = query
        self.messages.append({"role": "user", "content": content})
        logger.update("main_task", self.messages[-1])
        func_call = gpt4_functions(self.messages, funcs)
        self.messages.append(
            {"role": "assistant", "content": None, "function_call": func_call}
        )
        logger.update("main_task", self.messages[-1])
        func_name = func_call["name"]
        func_para = json.loads(func_call["arguments"])
        back_content = self.call_func(query, func_name, func_para)
        print(back_content)
        return self.func_chain(query, funcs, func_name, back_content)

    # function chain
    def func_chain(self, query, funcs, func_name, back_content):
        """
        Execute the function chain to solve the query.

        Args:
            query (str): The query to solve.
            funcs (list): The list of available functions.
            func_name (str): The name of the current function.
            back_content (str): The JSON-encoded content returned by the previous function.

        Returns:
            str: The final result of solving the query.
        """
        while True:
            self.messages.append(
                {"role": "function", "name": func_name, "content": back_content}
            )
            logger.update("main_task", self.messages[-1])
            func_call = gpt4_functions(self.messages, funcs)
            self.messages.append(
                {"role": "assistant", "content": None, "function_call": func_call}
            )
            logger.update("main_task", self.messages[-1])
            func_name = func_call["name"]
            func_para = json.loads(func_call["arguments"])
            if func_name == "finish":
                logger.update("result", func_para["result"])
                print_usage()
                logger.calculate_cost()
                self.container.stop()
                self.container.remove()
                return func_para["result"]

            back_content = self.call_func(query, func_name, func_para)
            sys.stdout.print_colored(back_content, "blue")

    def run(self, funcs):
        """
        Run the OpenAgent to solve the given query.

        Args:
            funcs (list): The list of available functions.
        """
        print(self.init_query)
        result = self.start_chain(self.init_query, funcs)
        print(result)
        self.container.stop()
        self.container.remove()


def main():
    """
    The main function to run the OpenAgent program.
    It parses the command-line arguments, initializes the OpenAgent, and runs it to solve the given query.
    """
    text = "OpenAgent"
    font = "ansi_shadow"
    ascii_art = pyfiglet.figlet_format(text, font=font)
    print("\n" + ascii_art)
    query = """Please use qlib(https://github.com/microsoft/qlib) to fulfill this task: I am a fintech researcher aiming to utilize data from the A market (csi500) spanning from 2008 to 2018 to train an LightGBM model, with the goal of forecasting market conditions for 2018 to 2019, and get its backtest result. You should not only give me the back test result, but also the transaction details in csv format of how to get such result."""
    identifier = os.getpid()

    sys.stdout = LoggerAndPrinter(identifier=str(identifier))
    my_parser = argparse.ArgumentParser(description="Pass the query")

    # Add the arguments
    my_parser.add_argument(
        "--query",
        metavar="query",
        type=str,
        help="the query to pass to the assistant",
        default=query,
    )
    my_parser.add_argument(
        "--gpt_version",
        metavar="gpt_version",
        type=str,
        help="the gpt version to use",
        default="gpt-4-0125-preview",
    )
    my_parser.add_argument(
        "--temperature",
        metavar="temperature",
        type=float,
        help="the temperature to use",
        default=0.7,
    )
    my_parser.add_argument(
        "--use_cache",
        action="store_true",
        help="whether to use cache (default: do not use cache)",
        default=False,
    )
    my_parser.add_argument(
        "--name",
        metavar="name",
        type=str,
        help="repository name",
        default="qlibb",
    )
    my_parser.add_argument(
        "--use_human_exp",
        action="store_true",
        help="whether to use cache (default: do not use cache)",
        default=False,
    )

    args = my_parser.parse_args()

    init_query = args.query
    use_cache = args.use_cache
    gpt4_version = args.gpt_version
    gpt_temperature = args.temperature
    repo_name = args.name
    gpt.version = gpt4_version
    gpt.temperature = gpt_temperature
    logger.init(
        init_query,
        datetime.now().strftime("%m-%d-%H-%M-%S"),
        use_cache,
        gpt4_version,
        gpt_temperature,
        repo_name,
        "GA",
    )

    assistant = OpenAgent(init_query, use_cache)
    assistant.run(functions)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_meg = str(e) + "\n" + traceback.format_exc()
        print(error_meg)
        logger.update("result", f"Exceptionally finished due to: {error_meg}")
        exit(1)
