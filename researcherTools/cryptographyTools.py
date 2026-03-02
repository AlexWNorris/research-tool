import json
import os
import hashlib
from cryptography.fernet import Fernet

_encryption_key = os.environ.get("ENCRYPTION_KEY").encode()
cipher_suite = Fernet(_encryption_key)

def decrypt_to_json(data):
    """
    take encrypted string and return original json string
    """
    encrypted_bytes = data.encode('utf-8')
    json_bytes = cipher_suite.decrypt(encrypted_bytes)
    json_string = json_bytes.decode('utf-8')
    formated_data = json.loads(json_string)

    return formated_data

def return_normalised_shar_hash(data):
    return hashlib.sha256(data.lower().strip().encode('utf-8')).hexdigest()
