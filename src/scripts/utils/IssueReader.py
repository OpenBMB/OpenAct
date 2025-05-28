import json
import re

import requests
from rich.console import Console
from rich.markdown import Markdown

from  logger import logger
from  utils.OpenaiAPI import GITHUB_TOKEN, gpt4

system = """You are a professional programmer. When using a github repository to solve a query, you meet a problem and you want to check the issues to solve it.
Now you will be given the initial query of using this repository and the problem you want to solve by checking the issues and the content of a issue of the repository. You need to judge whether the issue can solve the problem. If so, you should convert locate the significant part of the issue and tell the solution to the problem with the repository.

Format:

User:
Problem: <description of the problem to solve>
Issue: <content of the issue>

Assistant:
Judge: Yes/No (Whether the issue solve the problem)
Message: <(if Judge is Yes)the solution to the problem with the repository>/<(if Judge is No)None>
"""


def judge(problem, content, init_query):
    console = Console()
    console.print(Markdown(content))
    query = (
        "Problem: " + problem + "\nInit query: " + init_query + "\nIssue: " + content
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
    ]
    response = gpt4(messages)
    judgement = re.findall(r"Judge: (.+?)\n", response)[0] == "Yes"
    message = re.findall(r"Message: (.+?)$", response, re.DOTALL)[0]
    logger.update("issue_log", {"issue": content, "judgement": response})
    return judgement, message


def process_issue(issue, headers, owner, repo):
    issue_number = issue["number"]
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        issue_details = response.json()
        comments = []
        if issue_details["comments"] != 0:
            comments_url = issue_details["comments_url"]
            comments_response = requests.get(comments_url, headers=headers)
            if comments_response.status_code == 200:
                comments = comments_response.json()
            else:
                print(
                    f"Failed to retrieve comments for issue number {issue_number}: {comments_response.status_code}"
                )
        issue_details["comments_details"] = comments
        comment_content = ""
        for comment in comments:
            comment_content += (
                "\n## " + comment["user"]["login"] + ": \n" + comment["body"] + "\n"
            )
        issue_details["comment_content"] = comment_content
    else:
        print(
            f"Failed to retrieve issue details for issue number {issue_number}: {response.status_code}"
        )

    # Check if issue["body"] and issue_details['comment_content'] are not None before concatenating
    title = issue["title"] if issue["title"] else ""
    issue_body = issue["body"] if issue["body"] else ""
    comment_content = (
        issue_details["comment_content"] if issue_details["comment_content"] else ""
    )

    return str(
        "# Issue Title: "
        + title
        + "\n\n# "
        + issue["user"]["login"]
        + ": \n"
        + issue_body
        + "\n\n"
        + comment_content
    )


def read_issues(problem, owner, repo, init_query):
    logger.log["issue_log"].append({"problem": problem, "search_log": []})
    cnt = 0
    headers = {
        "Authorization": "token {}".format(GITHUB_TOKEN),
        "Accept": "application/vnd.github+json",
    }

    page = 1
    per_page = 30

    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues?page={page}&per_page={per_page}&state=all"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            issues = response.json()
            if not issues:
                break

            for issue in issues:
                cnt += 1
                if cnt == 50:
                    return json.dumps({"Result": "Relevant issue not found."})
                processed_content = process_issue(issue, headers, owner, repo)
                judgement, message = judge(problem, processed_content, init_query)
                if judgement:
                    return json.dumps({"Issue": processed_content, "Hint": message})
            page += 1
        else:
            print(f"Failed to retrieve issues: {response.status_code}")
            break

    return json.dumps({"Result": "Relevant issue not found."})