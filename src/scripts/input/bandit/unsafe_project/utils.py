# util.py
import base64


def encode_password(password):
    # 使用 base64 编码密码（不安全）
    return base64.b64encode(password.encode()).decode()
