import os
import shutil
from huggingface_hub import HfApi, snapshot_download, model_info
from transformers import pipeline

def clone_or_update_repo(repo_id, repo_dir):
    """
    Clone or update a Hugging Face repository to the specified directory.
    """
    if os.path.exists(repo_dir):
        print(f"Updating existing repository in {repo_dir}")
        shutil.rmtree(repo_dir)
    print(f"Cloning repository {repo_id} to {repo_dir}")
    snapshot_download(repo_id, local_dir=repo_dir)
    print(f"Repository cloned successfully to {repo_dir}")

def get_model_tags(repo_id):
    """
    Get the tags of a Hugging Face model repository.
    """
    info = model_info(repo_id)
    return info.tags

def download_file(repo_id, file_path, dest_path):
    """
    Download a specific file from a Hugging Face repository to the destination directory.
    """
    repo_dir = snapshot_download(repo_id)
    src_file = os.path.join(repo_dir, file_path)
    if os.path.exists(src_file):
        if not os.path.exists(os.path.dirname(dest_path)):
            os.makedirs(os.path.dirname(dest_path))
        shutil.copy(src_file, dest_path)
        print(f"File {file_path} copied to {dest_path}")
    else:
        print(f"File {file_path} does not exist in the repository.")

def download_folder(repo_id, folder_path, dest_path):
    """
    Download a specific folder from a Hugging Face repository to the destination directory.
    """
    repo_dir = snapshot_download(repo_id)
    src_folder = os.path.join(repo_dir, folder_path)
    if os.path.exists(src_folder):
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        shutil.copytree(src_folder, dest_path)
        print(f"Folder {folder_path} copied to {dest_path}")
    else:
        print(f"Folder {folder_path} does not exist in the repository.")

def use_pipeline(repo_id, task):
    """
    Use a Hugging Face pipeline for a specified task with the given repository.
    """
    pipe = pipeline(task, model=repo_id)
    return pipe

# if __name__ == "__main__":
#     REPO_ID = "bert-base-uncased"
#     REPO_DIR = "/path/to/huggingface/repository"
#     FILE_PATH = "vocab.txt"
#     FOLDER_PATH = "folder/in/repo"
#     DEST_PATH_FILE = "/path/to/destination/file.txt"
#     DEST_PATH_FOLDER = "/path/to/destination/folder"
#     TASK = "fill-mask"

#     clone_or_update_repo(REPO_ID, REPO_DIR)
    
#     tags = get_model_tags(REPO_ID)
#     print(f"Model tags: {tags}")

#     download_file(REPO_ID, FILE_PATH, DEST_PATH_FILE)
#     download_folder(REPO_ID, FOLDER_PATH, DEST_PATH_FOLDER)

#     pipe = use_pipeline(REPO_ID, TASK)
#     result = pipe("The capital of France is [MASK].")
#     print(result)
