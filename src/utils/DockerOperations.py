import io
import json
import os
import subprocess
import tarfile
import tempfile
import traceback
from pathlib import Path

import docker
import git

from  logger import logger

MAX_FILE_COUNT = 50


def get_container_by_attribute(attribute, value):
    """
    Get a Docker container by a specific attribute and value.

    :param attribute: The attribute to search for.
    :param value: The value to search for.
    """
    client = docker.from_env()
    containers = client.containers.list(all=True)

    for container in containers:
        if getattr(container, attribute, None) == value:
            return container

    return None


def dockerrename(container, old_path, new_path):
    """
    Rename a file or directory inside a Docker container.

    :param container: The Docker container object.
    :param old_path: The current path of the file or directory inside the container.
    :param new_path: The new desired path or name for the file or directory.
    """

    # Use mv command to rename a file or directory inside the container
    mv_cmd = f"mv {old_path} {new_path}"
    exit_code, output = container.exec_run(mv_cmd)
    if exit_code != 0:
        return json.dumps(
            {
                "Error": f"Failed to rename the file/directory inside the container. Output: {output.decode()}"
            }
        )
    return json.dumps({f"result": f"successfully renamed {old_path} to {new_path}"})


def build_and_run_container(container, dockerfile_path, repo_url):
    """
    Build a Docker image from a Dockerfile and run a container from that image.

    :param container: The Docker container object.
    :param dockerfile_path: The path to the Dockerfile inside the container.
    :param repo_url: Optional Git repository URL to clone before building.
    """
    exit_code, dockerfile_content = container.exec_run(["cat", dockerfile_path])
    if exit_code != 0:
        return 0, json.dumps({"Error": "Such file doesn't exist."}), 0
    file = dockerfile_content.decode("utf-8")
    return create_and_run_container_from_string(
        file, image_name="myimage", repo_url=repo_url
    )


def create_and_run_container_from_string(
    dockerfile_content, image_name="myimage", repo_url=None, container_name=None
):
    """
    Build a Docker image from a Dockerfile content string and run a container from that image.
    Optionally, clone a Git repository before building.

    :param dockerfile_content: Dockerfile content as a string.
    :param image_name: Name for the Docker image.
    :param container_name: Optional name for the Docker container. If not provided, Docker will generate one.
    :param repo_url: Optional Git repository URL to clone before building.
    :return: Running container object.
    """

    dockerfile_content = dockerfile_content.replace("CMD", "#CMD").replace(
        "ENTRYPOINT", "#ENTRYPOINT"
    )

    dockerfile_content += "\nWORKDIR /"

    print(dockerfile_content)

    # Create a Docker client
    client = docker.from_env()

    with tempfile.TemporaryDirectory() as tempdir:
        # Clone the repository if a URL is provided
        if repo_url:
            try:
                git.Repo.clone_from(repo_url, tempdir)
            except Exception as e:
                print("Failed to clone repository:")
                traceback.print_exc()
                return None, json.dumps({"error": str(e)}), dockerfile_content

        # Create the Dockerfile in the directory
        dockerfile_path = os.path.join(tempdir, "Dockerfile")
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)

        try:
            # Build the Docker image
            image, build_log = client.images.build(
                path=tempdir, tag=image_name, dockerfile="Dockerfile"
            )
            # Run the Docker container
            container = client.containers.run(
                image_name, name=container_name, detach=True
            )
            return (
                container,
                json.dumps({"result": "Docker container is built successfully."}),
                dockerfile_content,
            )

        except Exception as e:
            print("Error during Docker build/run:")
            traceback.print_exc()
            error_message = str(e).replace('"', '\\"').replace("\n", "\\n")
            return None, json.dumps({"error": error_message}), dockerfile_content


def dockerwrite_empty_file(container, file_path):
    """
    Write an empty file inside a Docker container.

    :param container: The Docker container object.
    :param file_path: The path where the empty file should be created inside the container.
    """
    # Ensure the destination directory exists
    dest_dir = os.path.dirname(file_path)
    mkdir_cmd = f"mkdir -p {dest_dir}"
    exit_code, output = container.exec_run(mkdir_cmd)

    # Create an empty file
    cmd = f"touch {file_path}"
    exit_code, output = container.exec_run(cmd)
    if exit_code != 0:
        print(output)
        return json.dumps(
            {
                "Error": f"Failed to create empty file inside the container. Output: {output.decode()}"
            }
        )
    return json.dumps({"result": f"Successfully created empty file at {file_path}"})


def dockerwrite(path, content, container, workdir="/"):
    """
    Write a file inside a Docker container.

    :param path: The path where the file should be created inside the container.
    :param content: The content to write to the file.
    :param container: The Docker container object.
    :param workdir: The working directory of the container.
    """
    tarstream = io.BytesIO()
    tar = tarfile.open(fileobj=tarstream, mode="w")
    file_data = content.encode("utf-8")
    tarinfo = tarfile.TarInfo(name="tempfile")
    tarinfo.size = len(file_data)
    tar.addfile(tarinfo, io.BytesIO(file_data))
    tar.close()
    tarstream.seek(0)

    if not workdir:
        workdir = "/"

    if not workdir.endswith("/"):
        workdir += "/"

    container.put_archive(path=workdir, data=tarstream)

    move_cmd = f"mv {workdir}tempfile {path}"
    exit_code, output = container.exec_run(move_cmd, workdir=workdir)

    if exit_code == 0:
        return True
    else:
        print(f"Error moving file: {output.decode('utf-8')}")

    try:
        content_escaped = content.replace('"', '\\"').replace("'", "\\'")
        write_cmd = f'echo "{content_escaped}" > "{path}"'
        exit_code, output = container.exec_run(write_cmd)

        if exit_code == 0:
            return True
        else:
            print(f"Error writing file: {output.decode('utf-8')}")
    except Exception as e:
        print(f"Exception during write: {e}")

    return False


def dockermkdir(container, directory_path):
    """
    Create a directory inside a Docker container.

    :param directory_path: The path where the directory should be created inside the container.
    :param container: The Docker container object.
    """

    # Use mkdir command to create a directory inside the container
    mkdir_cmd = f"mkdir -p {directory_path}"
    exit_code, output = container.exec_run(mkdir_cmd)
    if exit_code != 0:
        return json.dumps(
            {
                "Error": f"Failed to create directory inside the container. Output: {output.decode()}"
            }
        )
    return json.dumps({"result": f"successfully built directory at {directory_path}"})


def upload(container, local_folder_path, container_folder_path):
    """
    Upload a local folder to a Docker container.

    :param container: The Docker container object.
    :param local_folder_path: The path of the local folder to upload.
    :param container_folder_path: The path where the local folder should be uploaded inside the container.
    """
    container = container.id.strip("<>").split(": ")[-1]

    local_folder_path = Path(local_folder_path).resolve()

    if not local_folder_path.exists():
        return json.dumps(
            {"Error": f"Local folder '{local_folder_path}' does not exist."}
        )

    create_dir_command = [
        "docker",
        "exec",
        container,
        "mkdir",
        "-p",
        container_folder_path,
    ]
    try:
        subprocess.run(create_dir_command, check=True)
    except subprocess.CalledProcessError:
        return json.dumps({"Error": "Failed to create directory in the container."})

    docker_command = [
        "docker",
        "cp",
        str(local_folder_path),
        f"{container}:{container_folder_path}",
    ]
    try:
        subprocess.run(docker_command, check=True)
        return json.dumps(
            {"result": f"Successfully uploaded to `{container_folder_path}`."}
        )
    except subprocess.CalledProcessError as e:
        return json.dumps({"Error": "Docker command failed"})


def download(container, container_folder_path, local_folder_path):
    """
    Download a file or folder from a Docker container to the local machine.

    :param container: The Docker container object.
    :param container_folder_path: The path of the file or folder inside the container.
    :param local_folder_path: The path where the file or folder should be downloaded to on the local machine.
    """
    # Adjust local folder path based on conditions
    if local_folder_path[0] == "/":
        local_folder_path = "result" + local_folder_path

    if logger.signal:
        local_folder_path = "output/" + logger.signal + "/" + local_folder_path

    local_folder_path = local_folder_path.replace(":", "-")

    # Extract just the container ID or name in case it's formatted
    container = container.id.strip("<>").split(": ")[
        -1
    ]  # Adjust if container_id format is different

    # Check if container_folder_path exists in the container
    check_path_cmd = [
        "docker",
        "exec",
        container,
        "sh",
        "-c",
        f"test -e {container_folder_path}",
    ]
    try:
        subprocess.run(check_path_cmd, check=True)
    except subprocess.CalledProcessError:
        return json.dumps(
            {
                "Error": f"Path '{container_folder_path}' does not exist in the container."
            }
        )

    # Prepare local path, ensuring it exists
    local_path = Path(local_folder_path)
    if not local_path.exists():
        # Create the directory, including any necessary parent directories
        local_path.mkdir(parents=True, exist_ok=True)

    # Determine if the local path type should be a file or directory based on existence
    if local_path.exists() and local_path.is_dir():
        local_path = local_path / Path(container_folder_path).name

    # Perform the docker cp operation
    docker_command = [
        "docker",
        "cp",
        f"{container}:{container_folder_path}",
        str(local_path.parent),
    ]
    try:
        print(docker_command)
        subprocess.run(docker_command, check=True)
        return json.dumps(
            {
                "result": f"Successfully downloaded from `{container_folder_path}` to `{local_folder_path}`."
            }
        )
    except subprocess.CalledProcessError as e:
        error_msg = str(e) + traceback.format_exc()
        return json.dumps({"Error": error_msg})


def calculate_file_count(container, directory, MAX_FILE_COUNT=80):
    cmd = ["ls", "-a", directory]
    output = container.exec_run(cmd).output.decode("utf-8")
    entries = output.split("\n")[2:-1]
    file_count = 0

    for entry in entries:
        if file_count > MAX_FILE_COUNT:
            break
        if entry:
            entry_path = os.path.join(directory, entry)
            if container.exec_run(["test", "-e", entry_path]).exit_code == 0:
                if container.exec_run(["test", "-f", entry_path]).exit_code == 0:
                    file_count += 1
                elif container.exec_run(["test", "-d", entry_path]).exit_code == 0:
                    file_count += calculate_file_count(container, entry_path)

    return file_count


def subdir(container, start_directory):
    print(start_directory)
    cmd = ["ls", "-a", start_directory]
    output = container.exec_run(cmd).output.decode("utf-8")
    if "cannot access" in output:
        return "This path doesn't exist. Please study relevant bash commands in the readme file carefully and give me your modified path."
    entries = output.split("\n")[2:-1]
    subdirlist = []
    for entry in entries:
        if entry:
            entry_path = os.path.join(start_directory, entry)
            subdirlist.append(entry_path)
    return subdirlist


def explore_container_directory(container, start_directory, file_count, data={}):
    cmd = ["ls", "-a", start_directory]
    output = container.exec_run(cmd).output.decode("utf-8")
    if "cannot access" in output:
        return "This path doesn't exist. Please study relevant bash commands in the readme file carefully and give me your modified path."
    entries = output.split("\n")[2:-1]
    if not isinstance(file_count, int):
        file_count = 0
    if file_count < MAX_FILE_COUNT and file_count != 0:
        for entry in entries:
            if entry:
                entry_path = os.path.join(start_directory, entry)
                if container.exec_run(["test", "-f", entry_path]).exit_code == 0:
                    data[entry_path] = 0
                elif container.exec_run(["test", "-d", entry_path]).exit_code == 0:
                    dir_data = explore_container_directory(container, entry_path, {})
                    data[entry_path] = dir_data
    else:
        for entry in entries:
            if entry:
                entry_path = os.path.join(start_directory, entry)
                if container.exec_run(["test", "-f", entry_path]).exit_code == 0:
                    data[entry_path] = 0
                elif container.exec_run(["test", "-d", entry_path]).exit_code == 0:
                    dir_data = explore_container_directory(
                        container, entry_path, file_count, {}
                    )
                    data[entry_path] = dir_data
    return data
