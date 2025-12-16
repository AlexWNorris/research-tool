import os
import msal
import requests
import json

# Configuration
# Modes: 'PERSONAL' (Delegated) or 'ORGANIZATION' (Client Credentials)
AUTH_MODE = os.environ.get('ONEDRIVE_AUTH_MODE', 'PERSONAL').upper()

CLIENT_ID = os.environ.get('ONEDRIVE_CLIENT_ID')
CLIENT_SECRET = os.environ.get('ONEDRIVE_CLIENT_SECRET')
TENANT_ID = os.environ.get('ONEDRIVE_TENANT_ID')
USER_ID = os.environ.get('ONEDRIVE_USER_ID') # Required for Organization mode

# Cache file for Personal mode to avoid repeated logins
TOKEN_CACHE_FILE = 'token_cache.bin'

def _load_cache():
    cache = msal.SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE_FILE):
        cache.deserialize(open(TOKEN_CACHE_FILE, "r").read())
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        with open(TOKEN_CACHE_FILE, "w") as f:
            f.write(cache.serialize())

def get_access_token():
    """
    Acquires a token based on the configured AUTH_MODE.
    """
    if AUTH_MODE == 'PERSONAL':
        return _get_personal_token()
    elif AUTH_MODE == 'ORGANIZATION':
        return _get_org_token()
    else:
        print(f"Error: Unknown ONEDRIVE_AUTH_MODE '{AUTH_MODE}'. Use 'PERSONAL' or 'ORGANIZATION'.")
        return None

def _get_personal_token():
    """
    Delegated Flow (Public Client) for Personal Accounts.
    Uses 'common' authority and interactive login.
    """
    if not CLIENT_ID:
        print("Error: ONEDRIVE_CLIENT_ID is missing for Personal mode.")
        return None

    # Authority for personal accounts: 'consumers' forces Personal account login
    # 'common' allows both, but 'consumers' is stricter/safer for personal-only testing
    authority = "https://login.microsoftonline.com/consumers"
    scopes = ["Files.ReadWrite.All"]

    cache = _load_cache()
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=authority,
        token_cache=cache
    )

    # 1. Try to look up a token in cache
    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])

    # 2. If no suitable token in cache, let the user log in interactively
    if not result:
        print("No cached token found. Initiating interactive login...")
        # Note: This will open the system browser
        result = app.acquire_token_interactive(scopes=scopes)

    if "access_token" in result:
        _save_cache(cache)
        return result["access_token"]
    else:
        print(f"Error acquiring personal token: {result.get('error')}")
        print(result.get('error_description'))
        return None

def _get_org_token():
    """
    Client Credentials Flow (Daemon) for Organization Accounts.
    """
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
        print("Error: CLIENT_ID, CLIENT_SECRET, and TENANT_ID are required for Organization mode.")
        return None

    authority = f"https://login.microsoftonline.com/{TENANT_ID}"
    scope = ["https://graph.microsoft.com/.default"]

    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=authority,
        client_credential=CLIENT_SECRET,
    )

    result = app.acquire_token_for_client(scopes=scope)
    
    if "access_token" in result:
        return result["access_token"]
    else:
        print(f"Error acquiring org token: {result.get('error')}")
        return None

def upload_file(file_content, filename):
    """
    Uploads a file to OneDrive using Microsoft Graph API.
    """
    token = get_access_token()
    if not token:
        return False

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Construct URL based on mode
    if AUTH_MODE == 'PERSONAL':
        # Personal accounts can use /me
        url = f'https://graph.microsoft.com/v1.0/me/drive/root:/ResearchData/{filename}:/content'
    else:
        # Org accounts (Daemon) usually need to specify a user
        if not USER_ID:
             print("Warning: ONEDRIVE_USER_ID not set. Uploading to 'me' might fail in Org mode.")
             # Fallback, though likely to fail for Daemon without a user context
             url = f'https://graph.microsoft.com/v1.0/users/{USER_ID}/drive/root:/ResearchData/{filename}:/content'
        else:
             url = f'https://graph.microsoft.com/v1.0/users/{USER_ID}/drive/root:/ResearchData/{filename}:/content'

    try:
        print(f"Attempting upload to: {url}")
        response = requests.put(url, headers=headers, data=file_content)
        response.raise_for_status()
        print(f"Successfully uploaded {filename} to OneDrive.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to upload to OneDrive: {e}")
        if 'response' in locals() and response is not None:
             print(f"Response: {response.text}")
        return False
