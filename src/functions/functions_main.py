functions = [
    {
        "type": "function",
        "function": {
            "name": "search_by_query",
            "description": "If you want to search for github repositories under with a query, you can use this function",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "query": {
                        "type": "string",
                        "description": "The query you want to search for a github repository to solve. It should be detailed and precise",
                    },
                },
                "required": ["thought", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_repository",
            "description": "Set up the environment and prepare necessary data of a repository, you can use this function",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "repo_url": {
                        "type": "string",
                        "description": "Url of the repository you want to set up, formatted 'https://github.com/repo_owner/repo_name.git'",
                    },
                },
                "required": ["thought", "repo_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "apply",
            "description": "Apply a repository to solve a query, you can use this function",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "query": {
                        "type": "string",
                        "description": "the query you want to solve using this repository, it should be detailed and precise",
                    },
                    "continuePreviousProcess": {
                        "type": "boolean",
                        "description": "If you choose a repository that you have applied before, choose whether to continue from the previous apply process or start a new one",
                    },
                },
                "required": ["thought", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "If you think you have solved the query (usually when 'apply' function return you with a meaningful result), you should use this function",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Internal reasoning and thoughts of why you call this function based on your condition",
                    },
                    "result": {
                        "type": "string",
                        "description": "Your answer to the initial query, it should be detailed and precise",
                    },
                },
                "required": ["thought", "result"],
            },
        },
    },
]
