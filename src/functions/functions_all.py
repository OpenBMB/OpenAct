functions = [
    {
        "type": "function",
        "function": {
            "name": "use_existing_repository",
            "description": "If an existed repository can solve your problem, you can use this function to use it",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "repo_name": {
                        "type": "string",
                        "description": "name of the repository you want to try to use",
                    },
                },
                "required": ["thought", "repo_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_a_new_repository",
            "description": "If existed repositories cannot solve your problem, you can use this function to find a new tool",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "text": {
                        "type": "string",
                        "description": "If the query has designated a repository with its name, or you think you should search it by matching name or text, fill the text for searching it here. It should be of only one word.",
                    },
                    "topics": {
                        "type": "string",
                        "description": "If you think you can retrieve github topic to search from the query, fill the topics for searching it here. You should sort the topics by revelance, which means you should put more revelant topics in the front position. The topics should be separated by ', '.",
                    },
                },
                "required": ["thought"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_file_or_directory",
            "description": "Examine the content of a file or a directory. A very useful function to study the directory structure of the repository and the content of a file, you can use this function",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "target_path": {
                        "type": "string",
                        "description": "Path to the target file or directory. It should be an absolute path starts from `/`.",
                    },
                },
                "required": ["target_path", "thought"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_container_with_existed_dockerfile",
            "description": "Set up the container with an existed Dockerfile",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "path": {"type": "string", "description": "Path to the Dockerfile"},
                },
                "required": ["thought", "path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "modify_entire_file",
            "description": "Modify the entire file to meet the requirement, you can use this function if the entire file is not too long",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "target_path": {
                        "type": "string",
                        "description": "Path to the target file starting from repository's name",
                    },
                    "modified_file": {
                        "type": "string",
                        "description": "Entire content of modified file.",
                    },
                },
                "required": ["target_path", "modified_file", "thought"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "modify_a_function",
            "description": "If it is a python code file and you want to modify a function, you can use this function",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "target_path": {
                        "type": "string",
                        "description": "Path to the target file starting from repository's name",
                    },
                    "class_name": {
                        "type": "string",
                        "description": "It the function is a method of a class, you can transmit the class name here",
                    },
                    "function_name": {
                        "type": "string",
                        "description": "The name of the function you want to modify",
                    },
                    "parameters": {
                        "type": "string",
                        "description": "The parameter(s) of the function you want to modify, if there is no parameter, you can leave it empty",
                    },
                    "modified_function": {
                        "type": "string",
                        "description": "Entire content of modified function. There should be no indent before `def`.",
                    },
                },
                "required": [
                    "thought",
                    "target_path",
                    "function_name",
                    "modified_function",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_a_file",
            "description": "Write a file to meet some requirement, you can use this function",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file that you want to write, it should start from the repository's name",
                    },
                    "content": {
                        "type": "string",
                        "description": "Entire content of the created file.",
                    },
                },
                "required": ["thought", "file_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_pulls_to_solve_problem",
            "description": "If there is problem with the code of the original repository, you can use this function to read the pulls of the repository to try to find whether pull requests from other users may contain the right code, do not use this function without careful consideration",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "query": {
                        "type": "string",
                        "description": "query you want to solve by reading the pulls",
                    },
                },
                "required": ["thought", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_file_or_directory",
            "description": "Examine the content of a file or a directory, you can use this function",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "target_path": {
                        "type": "string",
                        "description": "Path to the target file or directory.",
                    },
                },
                "required": ["target_path", "thought"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute command(s), you can use this function",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "command": {
                        "type": "string",
                        "description": 'Command to execute. The command should be in format of `/bin/sh -c "cd <specific directory> && <commands to be executed in this directory>"`. Do not forget the closing quotation.',
                    },
                    "type": {
                        "type": "boolean",
                        "description": "If you are running this command to get the final result, choose yes.",
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "Whether you need to see the entire output of the command.",
                    },
                },
                "required": ["command", "thought", "type", "verbose"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_issues_to_solve_problem",
            "description": "If you can't solve a task and think it is due to the repository's own problem, you can use this function to read the issues of the repository to try to find a solution, do not use this function without careful consideration",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "query": {
                        "type": "string",
                        "description": "query you want to solve by reading the issues, it should be detailed and precise. It should focus what you need or what you are lack of. You can also describe your current condition and the problem you are facing here.",
                    },
                },
                "required": ["command", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "upload_directory_to_container",
            "description": "If you want to upload a directory from local to the container, you can use this function, it will automatically make a directory in the container if necessary",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "local_path": {
                        "type": "string",
                        "description": "local path of the directory or file you want to upload",
                    },
                    "container_path": {
                        "type": "string",
                        "description": "path in the container you want to upload the directory or file to, it should be the path of a directory but not a file",
                    },
                },
                "required": ["thought", "local_path", "container_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "download_directory_from_container",
            "description": "If you want to download a directory or file from the container to local, you can use this function, it will automatically make a directory in the local if necessary",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "container_path": {
                        "type": "string",
                        "description": "path in the container of the directory or file you want to download",
                    },
                    "local_path": {
                        "type": "string",
                        "description": "directory path in the local you want to download the directory to, it should be a relative path and end with a '/'",
                    },
                },
                "required": ["thought", "container_path", "local_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit",
            "description": "If you have solved all the requirements of the query, you should use this function",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "result": {
                        "type": "string",
                        "description": "Your answer to the initial query, it should be detailed and precise. If the main result is saved in a file, you should also describe the result in natural language here.",
                    },
                },
                "required": ["thought", "result"],
            },
        },
    },
]
