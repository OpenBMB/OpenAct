import json
import platform
import re
from pprint import pprint

import docker
import requests

from  logger import logger
from  utils.DockerOperations import dockerwrite, dockerwrite_empty_file
from  utils.OpenaiAPI import GITHUB_TOKEN, gpt4

system = """You are a professional programmer. When using a github repository, you met a problem and you want to check the pull requests to solve it.

Now you will be given the problem you want to solve by checking the pull requests and the content of a pull request of the repository. You need to judge whether the pull request is relevant to the query. If so, you should tell how this pull request can solve the problem with the repository. The diff of this pull request will be saved at `/pr_diff.txt`.

Format:

User:
Problem: <description of the problem to solve>
PR: <content of the PR>

Assistant:
Judge: Yes/No (Whether the PR solve the problem)
Thought: <Reason of your judgement>
Message: <(if Judge is Yes) how this pr would solve the problem>/<(if Judge is No)None>
"""


def judge(problem, content):
    print("PR:", content)
    query = "Problem: " + problem + "\nPR: " + content
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
    ]
    response = gpt4(messages)
    judgement = re.findall(r"Judge: (.+?)\n", response)[0] == "Yes"
    message = re.findall(r"Message: (.+?)$", response, re.DOTALL)[0]
    logger.update("PR_log", {"PR": content, "judgement": response})
    return judgement, message


def read_PRs(container, problem, owner, repo):
    logger.log["PR_log"].append({"problem": problem, "search_log": []})
    headers = {
        "Authorization": "token {}".format(GITHUB_TOKEN),
        "Accept": "application/vnd.github+json",
    }

    page = 1
    per_page = 30
    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls?page={page}&per_page={per_page}&state=all"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            PRs = response.json()

            if not PRs:
                break

            for PR in PRs:
                if not PR["body"] or PR["body"].strip() == "":
                    continue
                judgement, message = judge(problem, PR["body"])

                if judgement:
                    while True:
                        try:
                            diff = requests.get(PR["diff_url"], headers=headers)
                            break
                        except:
                            pass
                    diff = diff.text
                    dockerwrite_empty_file(container, "/pr_diff.txt")
                    dockerwrite("/pr_diff.txt", diff, container)
                    return json.dumps(
                        {
                            "Report": message
                            + "\nThe difference between this pull and the original repository is saved at `/pr_diff.txt`, you should refer to this file when modifying the original repository."
                        }
                    )
            page += 1
        else:
            print(f"Failed to retrieve PRs: {response.status_code}")
            break

    return json.dumps({"Result": "Relevant PR not found."})