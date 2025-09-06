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
]
