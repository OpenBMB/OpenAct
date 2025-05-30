# app.py
import subprocess

from db import get_user_password
from flask import Flask, request

app = Flask(__name__)


@app.route("/user")
def user():
    username = request.args.get("username")
    # 潜在的 SQL 注入
    password = get_user_password(username)
    return password


@app.route("/ping")
def ping():
    # 潜在的命令注入
    host = request.args.get("host")
    return subprocess.check_output(f"ping {host}", shell=True)


if __name__ == "__main__":
    app.run()
