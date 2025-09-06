import base64
import hashlib
import json
import os
import sys


class Logger:
    """
    This class is used to log the process of GitAgent, including query, datetime, search result, main task, 
    setup phase, apply phase, modify log, create log, issue log, PR log, download log, call error, usage, and total cost.
    """
    
    def __init__(self, query=None, datetime=None):
        """
        Initialize the logger with query and datetime.
        
        Args:
            query: The query of the GitAgent.
            datetime: The datetime of the GitAgent.
        """
        self.query = query
        self.datetime = datetime
        self.file_name = "buffer.txt"
        self.signal = None
        self.log = {
            "query": query,
            "use_cache": False,
            "datetime": datetime,
            "method": None,
            "gpt_version": "gpt-4-1106",
            "gpt_temperature": 0.7,
            "terminate_reason": None,
            "final_result": None,
            "search_result": [],
            "main_task": [],
            "search_phase": [],
            "setup_phase": [[]],
            "apply_phase": [[]],
            "modify_log": [],
            "modify_detail": [],
            "create_log": [],
            "issue_log": [],
            "PR_log": [],
            "download_log": [],
            "call_error": [],
            "usage": [],
            "total_cost": {
                "gpt-3.5-turbo": None,
                "gpt-4": None,
                "gpt-4-32k": None,
                "gpt-4-1106": None,
            },
        }
        self.queue = []
        self.tool_block_id = 0

    def init(
        self,
        query,
        datetime,
        use_cache=False,
        gpt_version="gpt-4-1106",
        gpt_temperature=0.7,
        repo_name="qlibb",
        method="GA",
    ):
        """
        Initialize the logger with more parameters.
        
        Args:
            query: The query of the GitAgent.
            datetime: The datetime of the GitAgent.
            use_cache: Whether to use cache.
            gpt_version: The version of GPT.
            gpt_temperature: The temperature of GPT.
            repo_name: The name of the repository.
            method: The method of the GitAgent.
        """
        self.log["query"] = query
        self.log["datetime"] = datetime
        self.log["use_cache"] = use_cache
        self.log["gpt_version"] = gpt_version
        self.log["gpt_temperature"] = gpt_temperature
        self.log["method"] = method
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:8]
        self.signal = f"{datetime}~{query_hash}"
        if not os.path.exists(f"logs/{repo_name}/"):
            os.makedirs(f"logs/{repo_name}/")
        self.file_name = f"logs/{repo_name}/{self.signal}.json"
        if not os.path.exists("logs"):
            os.makedirs("logs")
        self.write_log()

    def write_log(self):
        """
        Write the log to a file.
        """
        prepared_log = self._prepare_dict(self.log)

        with open(self.file_name, "w") as f:
            # try:
            #     f.write(json.dumps(prepared_log, indent=4, ensure_ascii=False))
            # except Exception as e:
            #     f.write(str(e))
            try:
                f.write(json.dumps(self.queue))
            except Exception as e:
                f.write(str(e))

    def add_to_queue(self, method_name: str, block_id, **kwargs):
        """
        Add a message to the queue.
        
        Args:
            method_name: The name of the method.
            block_id: The id of the block.
            **kwargs: Other parameters.
        """
        data = {
            "method_name": method_name,
            "block_id": block_id,
        }
        data.update(kwargs)
        self.queue.append(data)

    def _prepare_dict(self, d):
        """
        Prepare the dictionary for JSON serialization.
        
        Args:
            d: The dictionary to be prepared.
            
        Returns:
            The prepared dictionary.
        """
        prepared = {}
        for k, v in d.items():
            if isinstance(v, bytes):
                prepared[k] = base64.b64encode(v).decode("utf-8")
            elif isinstance(v, dict):
                prepared[k] = self._prepare_dict(v)
            elif isinstance(v, list):
                prepared[k] = [
                    self._prepare_dict(i) if isinstance(i, dict) else i for i in v
                ]
            else:
                prepared[k] = v
        return prepared

    def update(self, tag, message):
        """
        Update the log with a tag and a message.
        
        Args:
            tag: The tag of the message.
            message: The message to be logged.
        """
        if len(self.log["apply_phase"][-1]) > 30:
            sys.exit("Exceed the maximum number of apply phase")
        if len(self.log["setup_phase"][-1]) > 30:
            sys.exit("Exceed the maximum number of setup phase")
        if len(self.log["issue_log"]) >= 2 or len(self.log["PR_log"]) >= 2:
            sys.exit("Exceed the maximum number of issue or PR")
        if tag == "main_task":
            self.log["main_task"].append(message)
        elif tag == "search_phase":
            self.log["search_phase"][-1]["search_log"].append(message)
        elif tag == "search_result":
            self.log["search_result"].append(message)
            return self.write_log()
        elif tag == "setup_log":
            self.log["setup_phase"][-1].append(message)
        elif tag == "apply_phase":
            self.log["apply_phase"][-1].append(message)
        elif tag == "result":
            self.log["final_result"] = message
            self.add_to_queue("final_result", "final_result", output=message)
            return self.write_log()
        elif tag == "modify_log":
            self.log["modify_log"][-1].append(message)
        elif tag == "modify_detail":
            self.log["modify_detail"].append(message)
        elif tag == "download_log":
            self.log["download_log"].append(message)
        elif tag == "usage":
            self.log["usage"].append(message)
            self.calculate_cost()
            return self.write_log()
        elif tag == "issue_log":
            self.log["issue_log"][-1]["search_log"].append(message)
        elif tag == "PR_log":
            self.log["PR_log"][-1]["search_log"].append(message)
        elif tag == "create_log":
            self.log["create_log"].append(message)
        elif tag == "call_error":
            self.log["call_error"].append(message)
            return self.write_log()
        else:
            raise Exception(f"Tag {tag} not recognized.")
        if "role" in message.keys() and message["role"] == "function":
            self.add_to_queue(
                "on_tool_end",
                "tool-" + str(self.tool_block_id),
                output=message["content"],
                status=0,
                depth=0,
            )
        else:
            self.tool_block_id += 1
            block_id = "tool-" + str(self.tool_block_id)
            self.add_to_queue(
                "on_agent_action", block_id, action=tag, action_input=message["content"]
            )
            if "function_call" in message.keys():
                self.add_to_queue(
                    "on_tool_start",
                    block_id,
                    tool_name=message["function_call"]["name"],
                    tool_description="",
                    tool_input=message["function_call"]["arguments"],
                    depth=0,
                )
        self.write_log()

    def calculate_cost(self):
        """
        Calculate the cost of the GitAgent.
        """
        # Define the cost per token for different models
        costs = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-32k": {"input": 0.06, "output": 0.12},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            "gpt-4-1106": {"input": 0.01, "output": 0.03},
        }

        # Helper function to calculate cost
        def calculate_cost(model, total_input_tokens, total_output_tokens):
            cost_per_input_token = costs[model]["input"] / 1000
            cost_per_output_token = costs[model]["output"] / 1000

            total_input_cost = total_input_tokens * cost_per_input_token
            total_output_cost = total_output_tokens * cost_per_output_token

            return total_input_cost + total_output_cost

        # Calculate and update cost for each model
        for model in costs.keys():
            total_input_tokens = sum(
                item["prompt_tokens"] for item in self.log["usage"]
            )
            total_output_tokens = sum(
                item["completion_tokens"] for item in self.log["usage"]
            )
            total_cost = calculate_cost(model, total_input_tokens, total_output_tokens)
            self.log["total_cost"][model] = total_cost

        self.write_log()


logger = Logger()
