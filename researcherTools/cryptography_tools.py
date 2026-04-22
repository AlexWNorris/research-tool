"""
Cryptography utilities for encryption, decryption, and secure hashing.
"""
import json
import os
import hashlib
from cryptography.fernet import Fernet

_encryption_key = os.environ.get("ENCRYPTION_KEY").encode()
cipher_suite = Fernet(_encryption_key)

def decrypt_to_json(data):
    """
    Decrypts encrypted data string and returns the original JSON string as a dictionary.
    
    Args:
        data (str): The encrypted string.
        
    Returns:
        dict: The formatted JSON dictionary.
    """
    encrypted_bytes = data.encode('utf-8')
    json_bytes = cipher_suite.decrypt(encrypted_bytes)
    json_string = json_bytes.decode('utf-8')
    formated_data = json.loads(json_string)

    return formated_data

def return_normalised_sha256_hash(data):
    """
    Normalize string and return its SHA256 hex digest.
    
    Args:
        data (str): Input raw data string.
        
    Returns:
        str: Hexadecimal SHA256 digest string.
    """
    return hashlib.sha256(data.lower().strip().encode('utf-8')).hexdigest()
