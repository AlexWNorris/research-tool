import json
import os
from cryptography.fernet import Fernet

_encryption_key = os.environ.get("ENCRYPTION_KEY").encode()
cipher_suite = Fernet(_encryption_key)

def encrypt_json(data):
    """
    take json string and return encrypted string
    """
    json_string = json.dumps(data)
    json_bytes = json_string.encode('utf-8')
    encrypted_bytes = cipher_suite.encrypt(json_bytes)
    encrypted_string = encrypted_bytes.decode('utf-8')

    return encrypted_string

