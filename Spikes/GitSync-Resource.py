import requests
import os

# mkdir -p  /tmp/GitSync/Cache

# URL to the raw file on GitHub
file_url = 'https://github.com/Droidzzzio/speak/raw/refs/heads/master/speak.py'
local_path='/tmp/GitSync/Big'
local_file_path = local_path + '/' + 'speak.py'
etag_file_path = local_path + '/' + 'speak.py.etag'  # File to store the ETag

# Function to get the ETag from the file URL
def get_etag(file_url):
    response = requests.head(file_url, allow_redirects=True)  # HEAD request to get headers
    print('response.status_code:',response.status_code )
    print('response:',response )
    return response.headers.get('etag')

# Function to check if the ETag has changed
def has_etag_changed(local_etag_file, current_etag):
    if not os.path.exists(local_etag_file):
        return True  # If the ETag file doesn't exist, treat it as an update

    # Read the saved ETag from the file
    with open(local_etag_file, 'r') as f:
        saved_etag = f.read().strip()

    return saved_etag != current_etag

# Get the current ETag from GitHub
current_etag = get_etag(file_url)

if current_etag:
    if has_etag_changed(etag_file_path, current_etag):
        print("File has been updated. Downloading...")
        # Proceed to download the file
        response = requests.get(file_url, allow_redirects=True)
        with open(local_file_path, 'wb') as file:
            file.write(response.content)
        
        # Save the new ETag locally
        with open(etag_file_path, 'w') as f:
            f.write(current_etag)

        print("File downloaded successfully!")
    else:
        print("File is up to date!")
else:
    print("Couldn't get ETag.")
