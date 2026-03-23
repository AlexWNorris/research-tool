import os
import json
from cryptographyTools import decrypt_to_json

def get_content_from_text_file(file):
    with open(file) as fl:
        return fl.read()

def remove_leading_auto_warning_from_email_text(email_text):
    target_string = "CAUTION: This email originated from outside of the organisation. Do not click\nlinks or open attachments unless you recognise the sender and know the content\nis safe.\n"
    email_body = email_text.replace(target_string,"")
    return email_body

def get_encrypted_string_from_stored_data_file(file):
    file_content = get_content_from_text_file(file)
    encrypted_string = remove_leading_auto_warning_from_email_text(file_content)
    return encrypted_string

def save_to_folder(dir_path,filename,content):
    with open(dir_path+"/"+filename,"w") as fl:
        fl.write(content)

def populate_decrypted_folder_from(target_dir, output_dir="pilotData/decrypted"):
    files = os.listdir(target_dir)
    for file in files:
        path = target_dir+"/"+file
        encrypted_string = get_encrypted_string_from_stored_data_file(path)
        json_dict = decrypt_to_json(encrypted_string)
        json_string = json.dumps(json_dict)

        save_to_folder(output_dir,file,json_string)
def get_file_names_and_content_for_all_files_in_folder(target_dir):
    output = {}
    files = os.listdir(target_dir)
    for file in files:
        path = target_dir+"/"+file
        with open(path,"r") as fl:
            content = fl.read()
        output[file] = content
    return output