def insecure_file_access(user_input):
    with open(user_input, "r") as file:
        return file.read()
