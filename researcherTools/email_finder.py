"""
Utility for locating instances of specific email footprints across collected data.
"""
import file_handler
import cryptography_tools
import os
import json

def find_instances_of_email(target_email, data_dir):
    """
    Find instances of an email address across JSON log files.
    
    Args:
        target_email (str): The email address to look for.
        data_dir (str): Directory containing the data files.
        
    Returns:
        list: Names of matching files.
    """
    files = file_handler.get_file_names_and_content_for_all_files_in_folder(data_dir)
    hits=[]
    for file_name in files:
        json_dict = json.loads(files[file_name])
        stored_email = json_dict["survey_response"]["email"]
        hashed_email = cryptography_tools.return_normalised_sha256_hash(target_email)
        if stored_email == hashed_email:
            hits.append(file_name)
    return hits
