import hashlib


def insecure_hash(password):
    return hashlib.md5(password.encode()).hexdigest()
