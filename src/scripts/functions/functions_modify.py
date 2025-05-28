functions = [
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
                    "modification_query": {
                        "type": "string",
                        "description": "The query for modification, it should be detailed and precise. Only say what you are confident in, if there is no reason for the way of a modification, don't require it.",
                    },
                    "query_file_path": {
                        "type": "string",
                        "description": "It any query for modification is saved in a file, you can transmit the path of the file here",
                    },
                },
                "required": ["target_path", "modification_query", "thought"],
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
                    "modification_query": {
                        "type": "string",
                        "description": "The query for modification this function, it should be detailed and precise. Only say what you are confident in, if there is no reason for the way of a modification, don't require it.",
                    },
                },
                "required": [
                    "thought",
                    "target_path",
                    "function_name",
                    "modification_query",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit",
            "description": "If you think you have successfully modified the codes to meet the requirement, you can use this function",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    }
                },
                "required": ["thought"],
            },
        },
    },
]
