import json
import os
import re
import shutil

import git
import requests

from  Cacher import cache
from  functions.functions_dispatcher import functions
from  logger import logger
from  utils import (gpt4,gpt4_functions)


class RepoSearcher:
    """
    This class provides functions to search for appropriate GitHub repositories.
    """
    
    def __init__(self, token):
        """
        Initialize the RepoSearcher.
        
        Args:
            token (str): The GitHub access token.
        """
        self.token = token
        self.failed_repo = []
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
        }
        self.system_retrieve = """You are a professional programmer. Given a query, you want to find a github repository to solve this query. Firstly you need to search for the needed repository by their topics, which should be relevant to the query.

The topic name should be a noun. IF it contains many words, the words should be connected by '-'. If the query has concluded a realted topic, you should use it first.

Your answer should be in format as follows:

************
topic1, topic2, topic3, ...
************"""
        self.system_judge = """You are a professional programmer. Given a query and the readme file of a github repository, your task is to assess whether this repository is suitable to solve this query. You should evaluate whether the functionality of the repository aligns with the requirements of the query.

Note that the repository shouldn't be a software or an online platform, it should be a program that can be downloaded to setup and run with command line commands.

The readme must contains how to set up the environment and how to use it with command line commands. The repository should be code_based but not API_based.

If the readme doesn't contain command line commands to run existing program(s) to use the functions of this repository to solve the query, your judge must be No.

Your response should be structured as follows:

Reason: <reason of your judgement>
Judge: Yes/No"""
        self.system_dispatch = """You are a professional programmer. Given a task, you want to find a github repository to solve the task. Now, your colleagues have explored some repositories. If you think any of the repository(s) might can solve your task, call `use_existing_repository` function to use it. Otherwise, call `find_a_new_repository` function to find another repository.

You will be given the query of the task and name(s) and description(s) of existed repositories."""

    def retrieve_through_topic(self, topic):
        """
        Retrieve repositories based on a topic using the GitHub API.
        
        Args:
            topic (str): The topic to search for.
            
        Return:
            dict: The response data containing the retrieved repositories.
        """
        url = f"https://api.github.com/search/repositories?q=topic:{topic}&per_page=50"

        response = requests.get(url, headers=self.headers)
        response_data = response.json()
        if response.status_code == 200:
            print(
                "Successfully get {} repos related to {}.".format(
                    len(response_data["items"]), topic
                )
            )
            return response_data
        else:
            print(f"Request failed with status code {response.status_code}")

    def retrieve_through_text(self, text):
        """
        Retrieve repositories based on a text query using the GitHub API.
        
        Args:
            text (str): The text query to search for.
            
        Return:
            dict: The response data containing the retrieved repositories.
        """
        url = f"https://api.github.com/search/repositories?q={text}"

        response = requests.get(url, headers=self.headers)
        response_data = response.json()
        if response.status_code == 200:
            print(
                "Successfully get {} repos related to {}.".format(
                    len(response_data["items"]), text
                )
            )
            return response_data
        else:
            print(f"Request failed with status code {response.status_code}")

    def judge(self, repo, query):
        """
        Judge whether a repository is suitable for solving a query based on its README.
        
        Args:
            repo (dict): The repository information.
            query (str): The query to solve.
            
        Return:
            tuple: A tuple containing the judgment result, repository name, and repository URL.
        """
        repo_url = repo["clone_url"]
        repo_name = repo["name"]
        if repo_url in self.failed_repo:
            return False, None, None
        clone_destination = "repos/" + repo_name
        try:
            git.Repo.clone_from((repo_url), clone_destination)
        except Exception as e:
            print(e)
        try:
            for file in os.listdir(clone_destination):
                if "readme" in file.lower():
                    file_path = os.path.join(clone_destination, file)
                    print(file_path)
                    with open(file_path, "r") as f:
                        readme = f.read()
                    break
            content = str(
                "Query:'''"
                + query
                + "'''\n\nReadme of the repository:'''"
                + readme[:15000]
                + "...'''"
            )
            messages = [
                {"role": "system", "content": self.system_judge},
                {"role": "user", "content": content},
            ]
            response = gpt4(messages)
            logger.update(
                "search_phase", {"repo_name": repo_name, "response": response}
            )
            judgement = re.findall(r"Judge: (\w+)$", response)[0]
            if judgement != "No":
                return True, repo_name, repo_url
            else:
                self.failed_repo.append(repo_url)
                return False, None, None
        except Exception:
            return False, None, None
        finally:
            shutil.rmtree(clone_destination, ignore_errors=True)

    def search_by_text(self, text):
        """
        Search for a suitable repository based on a text query.
        
        Args:
            text (str): The text query to search for.
            
        Return:
            tuple: A tuple containing the repository name and URL, or (None, None) if not found.
        """
        logger.log["search_phase"].append({"text": text, "search_log": []})
        response_data = self.retrieve_through_text(text)
        if not response_data:
            return None, None
        for repo in response_data["items"]:
            judge, repo_name, repo_url = self.judge(repo, text)
            if judge:
                return repo_name, repo_url

    def judge_topic(self, topic, query):
        """
        Search for a suitable repository based on a topic.
        
        Args:
            topic (str): The topic to search for.
            query (str): The query to solve.
            
        Return:
            tuple: A tuple containing the repository name and URL, or (None, None) if not found.
        """
        logger.log["search_phase"].append({"topic": topic, "search_log": []})
        response_data = self.retrieve_through_topic(topic)
        if not response_data:
            return None, None
        for repo in response_data["items"]:
            judge, repo_name, repo_url = self.judge(repo, query)
            if judge:
                return repo_name, repo_url
        else:
            return None, None

    def search_by_topic(self, query):
        """
        Search for a suitable repository based on topics derived from the query.
        
        Args:
            query (str): The query to solve.
            
        Return:
            tuple: A tuple containing the repository name and URL, or (None, None) if not found.
        """
        messages = [
            {"role": "system", "content": self.system_retrieve},
            {"role": "user", "content": query},
        ]

        response = gpt4(messages)
        try:
            topics = re.findall(r"\*\n(.+?)\n\*", response)[0].split(", ")
        except:
            topics = response.split(", ")
        print(topics)

        for topic in topics:
            repo_name, repo_url = self.judge_topic(topic, query)
            if repo_name:
                return repo_name, repo_url

    def search_by_query(self, query, use_cache=True):
        """
        Search for a suitable repository based on the given query.
        
        Args:
            query (str): The query to solve.
            use_cache (bool, optional): Whether to use cached repository information. Default is True.
            
        Return:
            tuple: A tuple containing the repository name and URL, or (None, None) if not found.
        """
        temp_func = functions
        content = "Query: " + query
        if (
            use_cache
            and cache != {}
            and any(
                "description" in repo and repo["description"] is not None
                for repo in cache.values()
            )
        ):
            sys_prompt = self.system_dispatch
            repo_list = list(cache.keys())
            temp_func[0]["function"]["parameters"]["properties"]["repo_name"][
                "enum"
            ] = repo_list
            for repo_name, repo in cache.items():
                if "description" in repo and repo["description"] is not None:
                    content += (
                        "\nRepository's name: "
                        + repo_name
                        + "\nDescription: "
                        + repo["description"]
                        + "\n\n"
                    )
        else:
            sys_prompt = "You are a professional programmer. Given a task, you want to find a github repository to solve the task."
            temp_func = temp_func[1:]
            temp_func[0]["function"]["name"] = "find_a_proper_repository"
            temp_func[0]["function"][
                "description"
            ] = "Find the proper repository to solve the task through text or topic."
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": content},
        ]
        func_call = gpt4_functions(messages, temp_func)
        func_name = func_call["name"]
        func_para = json.loads(func_call["arguments"])
        if func_name == "use_existing_repository":
            repo_name = func_para["repo_name"]
            repo_url = cache[repo_name]["url"]
            return repo_name, repo_url
        if "text" in func_para:
            try:
                text = func_para["text"]
                repo_name, repo_url = self.search_by_text(text)
                if repo_name and repo_url:
                    return repo_name, repo_url
            except Exception as e:
                print(e)
                pass
        return self.search_by_topic(query)