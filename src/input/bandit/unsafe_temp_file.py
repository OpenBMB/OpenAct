import os
import tempfile


def insecure_temp_file():
    temp_file_path = tempfile.mktemp()
    print("Temporary file created at:", temp_file_path)

    with open(temp_file_path, "w") as temp_file:
        temp_file.write("Some sensitive data")

    with open(temp_file_path, "r") as temp_file:
        print("Temporary file content:", temp_file.read())

    os.remove(temp_file_path)
    print("Temporary file deleted")


insecure_temp_file()
