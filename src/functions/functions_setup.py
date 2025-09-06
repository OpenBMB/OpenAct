functions = [
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute one or more commands",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "command": {
                        "type": "string",
                        "description": 'Commands to execute. Every single should be in format of `/bin/sh -c "cd <specific directory> && <commands to be executed in this directory>"`. Do not forget the closing quotation.',
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "Whether you need to see the entire output of the command.",
                    },
                },
                "required": ["thought", "command", "verbose"],
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
            "name": "modify_file_content",
            "description": "Make modification to the content of a file to meet the requirement, you can use this function.",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "target_path": {
                        "type": "string",
                        "description": "Path to the target file you are going to modify which that starts from repository's name",
                    },
                    "modification_query": {
                        "type": "string",
                        "description": "The query for modification, it should be detailed and precise. If any message for modification is saved in a file, the path should also be contained.",
                    },
                    "continuePreviousProcess": {
                        "type": "boolean",
                        "description": "If you are to modify a file that you have modified before, choose whether to continue from the previous modification process or start a new one",
                    },
                },
                "required": ["target_path", "modification_query", "thought"],
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
                    "requirements": {
                        "type": "string",
                        "description": "The requirements of writing the file, it should be detailed and precise",
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
            "name": "submit",
            "description": "If you think you have successfully set up the environment and prepared the necessary data, you can use this function",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "path_to_report": {
                        "type": "string",
                        "description": "If you downloaded required data whose path isn't appointed by the readme and you decided it yourself, you should report what you have downloaded and where you have saved it in natural language here. It should be precise and detailed. You should give the complete absolute path of the data. It can be formatted like '<data_name> is downloaded with <command> to <path(absolute path)>.'",
                    },
                    "work_directory": {
                        "type": "string",
                        "description": "Default working directory is `/<repo_name>`, if you have set the environment with existed dockerfile and the working directory in the dockerfile is not so, you should report it here. It is where the content of the repo is saved. You must check the content of the dockerfile to confirm it. If you didn't set the environment with existing dockerfile, you don't need to fill this property.",
                    },
                },
                "required": ["thought"],
            },
        },
    },
]
