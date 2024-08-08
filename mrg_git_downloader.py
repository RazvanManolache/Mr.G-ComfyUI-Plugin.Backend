import os
import shutil
import git


def clone_or_update_repo(repo_url, repo_dir):
    """
    Clone a Git repository if it doesn't exist in the specified directory,
    or update it if it already exists.
    """
    if os.path.exists(repo_dir):
        try:
            repo = git.Repo(repo_dir)
            if not repo.bare:
                print(f"Updating existing repository in {repo_dir}")
                origin = repo.remotes.origin
                origin.pull()
                print("Repository updated successfully.")
            else:
                print(f"Repository directory {repo_dir} is empty.")
        except git.exc.InvalidGitRepositoryError:
            print(f"Directory {repo_dir} is not a valid repository. Cloning afresh.")
            repo = git.Repo.clone_from(repo_url, repo_dir)
            print(f"Repository cloned successfully to {repo_dir}.")
    else:
        print(f"Cloning repository to {repo_dir}")
        repo = git.Repo.clone_from(repo_url, repo_dir)
        print(f"Repository cloned successfully to {repo_dir}.")
    
def get_current_commit_hash(repo_dir):
    """
    Get the current commit hash of the repository in the specified directory.
    """
    try:
        repo = git.Repo(repo_dir)
        if not repo.bare:
            commit_hash = repo.head.commit.hexsha
            return commit_hash
        else:
            print(f"Repository directory {repo_dir} is empty.")
            return None
    except git.exc.InvalidGitRepositoryError:
        print(f"Directory {repo_dir} is not a valid repository.")
        return None

def copy_file_from_repo(repo_dir, file_path, dest_path):
    """
    Copy a specific file from the repository to the destination directory.
    """
    src_file = os.path.join(repo_dir, file_path)
    if os.path.exists(src_file):
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        shutil.copy(src_file, dest_path)
        print(f"File {file_path} copied to {dest_path}")
    else:
        print(f"File {file_path} does not exist in the repository.")

def copy_folder_from_repo(repo_dir, folder_path, dest_path):
    """
    Copy a specific folder from the repository to the destination directory.
    """
    src_folder = os.path.join(repo_dir, folder_path)
    if os.path.exists(src_folder):
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        shutil.copytree(src_folder, dest_path)
        print(f"Folder {folder_path} copied to {dest_path}")
    else:
        print(f"Folder {folder_path} does not exist in the repository.")

# if __name__ == "__main__":
#     REPO_URL = "https://github.com/your-repository-url.git"
#     REPO_DIR = "/path/to/your/repository"
#     FILE_PATH = "path/to/your/file/in/repo.txt"
#     FOLDER_PATH = "path/to/your/folder/in/repo"
#     DEST_PATH_FILE = "/path/to/destination/file"
#     DEST_PATH_FOLDER = "/path/to/destination/folder"

#     clone_or_update_repo(REPO_URL, REPO_DIR)
#     commit_hash = get_current_commit_hash(REPO_DIR)
    
#     if commit_hash:
#         print(f"Current commit hash: {commit_hash}")
    
#     copy_file_from_repo(REPO_DIR, FILE_PATH, DEST_PATH_FILE)
#     copy_folder_from_repo(REPO_DIR, FOLDER_PATH, DEST_PATH_FOLDER)
