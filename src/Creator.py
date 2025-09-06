import json
import re

from  functions.functions_modify import functions
from  logger import logger
from  utils import dockerwrite, dockerwrite_empty_file, gpt4, sys


class Creator:
    """
    This class is used to create files in a Docker container based on user queries.
    It uses the OpenAI GPT-4 model to generate code snippets.
    """
    def __init__(self, container, repo_name, work_dir):
        """
        Initialize the Creator class.

        Args:
            container: Docker container object.
            repo_name: Name of the repository.
            work_dir: Working directory inside the container.
        """
        self.container = container
        self.repo_name = repo_name
        self.workdir = work_dir

    def direct_create(self, requirement, target_path, path=None):
        """
        Create a file based on the user's query.

        Args:
            requirement: User's query or requirement for the file.
            target_path: Path where the generated file will be saved.
            path: Optional path to an existing file to refer to or imitate.

        Returns:
            JSON response indicating the result of the file creation process.
        """
        system_cre = """You are a professional programmer. You will be given a query to write a code file. You should give me the complete file with no omit.

Your response should be structured as follows:
The created file is:
\'\'\'
<content of the created file>
\'\'\'"""

        content = "Request: " + requirement

        if path:
            if self.container.exec_run(["test", "-f", path]).exit_code == 0:
                file_content = self.container.exec_run(["cat", path]).output.decode(
                    "utf-8"
                )
                system_cre = """You are a professional programmer. You will be given a query and a file. Your task is to imitate or refer to the given file to write a code file to complete the query. You should give me the complete file with no omit.
                
Your response should be structured as follows:
The created file is:
\'\'\'
<content of the created file>
\'\'\'
"""

                content += (
                    f"\nContent of the file to refer to ({path}): \n'''\n"
                    + file_content
                    + "\n'''"
                )
            else:
                content = "This path_of_file_to_refer_to doesn't exist."
                return json.dumps({"Error": content})

        message = [
            {"role": "system", "content": system_cre},
            {"role": "user", "content": content},
        ]

        response = gpt4(message)

        try:
            code = re.findall(r"'''.*?\n(.+?)'''", response, re.DOTALL)[0].strip()
        except:
            code = re.findall(r"```.*?\n(.+?)```", response, re.DOTALL)[0].strip()

        logger.update(
            "create_log",
            {
                "request": requirement,
                "path": target_path,
                "refer_path": path,
                "code": code,
            },
        )
        dockerwrite_empty_file(self.container, target_path)
        dockerwrite(target_path, code, self.container, self.workdir)
        return json.dumps({"Result": "Required file has been created and written."})
