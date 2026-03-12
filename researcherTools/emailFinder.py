import fileHandler
import cryptographyTools
import os
import json

def find_instances_of_email(target_email,data_dir):
    files = fileHandler.get_file_names_and_content_for_all_files_in_folder(data_dir)
    hits=[]
    for file_name in files:
        json_dict = json.loads(files[file_name])
        stored_email = json_dict["survey_response"]["email"]
        hashed_email = cryptographyTools.return_normalised_shar_hash(target_email)
        if stored_email == hashed_email:
            hits.append(file_name)
    return hits
