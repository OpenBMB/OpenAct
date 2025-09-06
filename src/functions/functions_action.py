functions = [
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
            "name": "modify_file_content",
            "description": "Make modification to the content of a file to meet the requirement, you can use this function",
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
                    "modification_query": {
                        "type": "string",
                        "description": "The query for modification, it should be detailed and precise",
                    },
                    "issue_derived": {
                        "type": "boolean",
                        "description": "If the query of this modification is derived from an issue, set this to true",
                    },
                    "continuePreviousProcess": {
                        "type": "boolean",
                        "description": "If you are to modify a file that you have modified before, choose whether to continue from the previous modification process or start a new one",
                    },
                },
                "required": [
                    "target_path",
                    "modification_query",
                    "thought",
                    "issue_derived",
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
                        "description": "Path to the file that you want to write, it should be a absolute path starts from `/`.",
                    },
                    "requirements": {
                        "type": "string",
                        "description": "The requirements of writing the file, it should be detailed and precise, it should include required format if necessary",
                    },
                    "path_of_file_to_refer_to": {
                        "type": "string",
                        "description": "If you want to imitate or refer to a file when writing the new file, you should pass the path of the file to be imitated or refered to here",
                    },
                },
                "required": ["thought", "file_path", "requirements"],
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
