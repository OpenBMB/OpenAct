from cryptography.fernet import Fernet


def encrypt_data(data):
    key = b"mysecretpassword"  # 应该使用更安全的方式来生成和存储密钥
    cipher_suite = Fernet(key)
    encrypted_data = cipher_suite.encrypt(data)
    return encrypted_data
