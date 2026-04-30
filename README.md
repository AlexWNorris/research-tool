# Web Privacy For Whom - README

Welcome to the repository for the Browser Fingerprinting Risk Analysis project. This README is intended to provide a overview of the codebase architecture, file purposes, and asset locations to assist with navigation.

The codebase is broadly divided into two main components:
1. **Web Application (`webApp/`)**: A Flask-based platform used to collect browser fingerprints and demographic survey data from participants securely.
2. **Researcher Tools (`researcherTools/`)**: A suite of scripts used to process, decrypt, and perform statistical/machine-learning analyses on the collected dataset.

---

## Directory Structure & File Purposes

### 1. Root Directory (`/`)
The root directory contains the overarching project files and configurations.
* **`requirements.txt`**: The pip dependencies required to run both the web application and the researcher tools. 


### 2. Web Application (`/webApp/`)
This directory contains the data collection platform.
* **`flask_app.py`**: The main Flask application that serves pages, handles routing, and processes incoming fingerprint/survey submissions.
* **`encryptor.py`**: Handles the encryption of sensitive user data at the point of collection before it is passed to the data pipeline.
* **`emailer.py`**: Utility script for dispatching automated emails used in the data pipeline.
* **`/templates/`**: Contains the HTML templates for the web app:
  * `consent.html`: The initial informed consent form.
  * `survey.html`: The demographic data collection form.
  * `fingerprint.html`: The core page where client-side JavaScript extracts the browser fingerprint.
  * `thankyou.html`: The final confirmation page.
  * `base.html`: The base HTML layout inherited by other pages.
* **`/static/`**: Contains the static web assets (`css/`, `js/`, `img/`) used by the HTML templates.

### 3. Researcher Tools (`/researcherTools/`)
This directory contains the Python scripts used to process and analyze the collected data.
* **`hub_tool.py`**: Provides rudimentary GUI for decrypting targeted files and running initial analyses on target directories, instead of the default directories defined in the bellow files.
* **`agglomerated_analysis.py`**: A core analysis script that quantifies browser fingerprinting risk by calculating informational entropy across demographic groups (Gender, Age, Income, Education). It conducts statistical significance testing (Mann-Whitney U) and produces combined risk charts as  output.
* **`advanced_eda.py`**: Performs exploratory data analysis (EDA) on the fingerprint dataset to producing a range of plots used for data understanding during analysis.
* **`rule_based_classification.py`**: Implements a rule-based classification system using decision trees to predict demographic categories directly from browser fingerprint attributes.
* **`data_handler.py` & `file_handler.py`**: Utility modules responsible for standardizing data ingestion, cleaning non-informative responses (e.g., 'Prefer not to say'), and file I/O operations.
* **`cryptography_tools.py`**: Handles the decryption of the dataset stored in the `fullData/encrypted/` directory.
* **`email_finder.py`**: Utility to securely look up email hashes within the dataset. Enabling user withdrawal after participation with the online data collection tool.

---


## Running the Project
This codebase omits environment variables required for the project to run. 

Therefore, to run the project, please refer to the OneDrive Codebase link, provided in the submission document.
