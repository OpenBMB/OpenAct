import threading
import time

import docker


class ExecRunResult:
    def __init__(self, exit_code, output):
        self.exit_code = exit_code
        self.output = output

    def __iter__(self):
        return iter((self.exit_code, self.output))


class EnhancedContainer(docker.models.containers.Container):
    def __init__(self, container, client=None):
        self.__dict__ = container.__dict__.copy()
        self.client = client

    def exec_run(self, cmd, max_retries=5, delay=2, timeout=1200, **kwargs):
        parent_exec_run = (
            super().exec_run
        )  # Assign parent class method to a local variable
        parent_restart = (
            super().restart
        )  # Assign parent class method to a local variable

        def target():
            nonlocal delay
            try:
                exit_code, output = parent_exec_run(
                    cmd, **kwargs
                )  # Use the local variable instead of super()
                self.result = ExecRunResult(exit_code, output)
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                print(
                    f"before start: {self.id}, {self.client.containers.get(self.id).status}"
                )
                parent_restart()  # Use the local variable instead of super()

                stop_time = 3
                elapsed_time = 0
                while (
                    self.client.containers.get(self.id).status != "running"
                    and elapsed_time < 60
                ):
                    time.sleep(stop_time)
                    elapsed_time += stop_time
                    print(f"{self.id}, {self.client.containers.get(self.id).status}")

                time.sleep(delay)
                delay *= 2  # Exponential backoff

        for attempt in range(max_retries):
            thread = threading.Thread(target=target)
            thread.start()
            thread.join(timeout)
            if thread.is_alive():
                print(f"Command execution timeout after {timeout} seconds.")
                thread._stop()
                return ExecRunResult(-1, "Command execution timeout".encode())
            else:
                if (
                    hasattr(self, "result") and self.result.exit_code != 0.5
                ):  # Check if result is set
                    return self.result

        return ExecRunResult(-1, "Error occurs: All attempts failed".encode())
