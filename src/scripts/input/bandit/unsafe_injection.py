import os


def unsafe_command_execution(user_input):
    command = "echo " + user_input
    os.system(command)
