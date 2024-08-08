import requests
import os

def download_file_from_url(url, dest_folder):
    """
    Download a file from a URL to the specified destination folder.
    """
    response = requests.get(url)
    if response.status_code == 200:
        file_name = url.split("/")[-1]
        dest_path = os.path.join(dest_folder, file_name)
        with open(dest_path, "wb") as file:
            file.write(response.content)
        print(f"File downloaded to {dest_path}")
        return True
    else:
        print(f"Failed to download file from {url}")
        return False