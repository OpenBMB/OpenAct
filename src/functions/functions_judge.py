functions = [
    {
        "type": "function",
        "function": {
            "name": "compare_images",
            "description": "Calculate the similarity between two images, you can use this function",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "path1": {
                        "type": "string",
                        "description": "Path to the first image",
                    },
                    "path2": {
                        "type": "string",
                        "description": "Path to the second image",
                    },
                },
                "required": ["thought", "path1", "path2"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_file_or_directory",
            "description": "Examine the content of a file or a directory, you can use this function. Note that this function is used to check file or directory in local, donnot pass path in the container.",
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
            "name": "calculate_md5",
            "description": "Calculate the md5 hash value of a file, you can use this function",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "target_path": {
                        "type": "string",
                        "description": "Path to the file that you want to calculate the md5 hash value.",
                    },
                },
                "required": ["thought", "target_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_score",
            "description": "Submit your calculated score of the outcome, you can use this function",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "score": {
                        "type": "integer",
                        "enum": [0, 1, 2, 3, 4, 5],
                        "description": "The score you give to the outcome",
                    },
                },
                "required": ["thought", "score"],
            },
        },
    },
]
