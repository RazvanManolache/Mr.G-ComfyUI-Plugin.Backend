import os
import folder_paths
import git


from . import mrg_git_downloader
from . import mrg_database
from . import mrg_helpers

def is_package_file_in_folder(folder_name, filename):
    if folder_paths.get_full_path(folder_name, filename):
        return True
    return False


def download_package_file(typ, link, filename, folder_name):
    real_folder = folder_paths.get_folder_paths(folder_name)
    match typ:
        case "git":
            mrg_git_downloader.download_file(link, filename, real_folder)
            return True
        case "huggingface":
            mrg_git_downloader.download_file(link, filename, real_folder)
            return True
        case "url":
            return False
            pass
    return False

            

def get_available_packages_from_repositories():
    package_repositories = mrg_database.get_package_repositories()
    all_packages = []
    for package_repository in package_repositories:
        packages = get_available_packages_from_repository(package_repository.uuid)
        for package in packages:
            if package.uuid not in [p.uuid for p in all_packages]:
                all_packages.append(package)
    return all_packages
    

def get_available_packages_from_repository(uuid):
    all_packages = []
    package_repository = update_package_repository(uuid)
    if package_repository is None:
        return all_packages
    repo_path = get_package_repository_path(uuid)
    
    json_files = []
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))
                
    # read the json files as packages
  
    for json_file in json_files:
        packages = mrg_helpers.read_json(json_file)
        # add only if package uuid does not exist in all_packages uuids
        if packages:
            for package in packages:
                try:
                    package_obj = mrg_database.dict_to_model(mrg_database.packages, package)
                except:
                    continue
                if package_obj:
                    if package_obj.uuid not in [p.uuid for p in all_packages]:
                        package_obj.package_repository_uuid = package_repository.uuid
                        package_obj.repository = package_repository.name
                        all_packages.append(package_obj)
    return all_packages
            
            
            
    
# 
def get_package_repository_path(uuid):
    # return a path relative to the root of the project, under package_repositories folder, uuid as folder name, create folder if it does not exist
    root_path = mrg_helpers.get_current_path()
    package_repositories_path = os.path.join(root_path, "package_repositories")
    # create the folder if it does not exist
    if not os.path.exists(package_repositories_path):
        os.makedirs(package_repositories_path)
    return  os.path.join(package_repositories_path, uuid)


# download or update package repository from github
def update_package_repository(uuid):
    package_repository = mrg_database.get_package_repository(uuid)
    if package_repository is None:
        return None
    if package_repository.url == "":
        return None
   
    
   
    repo_path = get_package_repository_path(uuid)
    if os.path.exists(repo_path):
        repo = git.Repo(repo_path)
        repo.remotes.origin.pull()
        return package_repository
    
    download_package_repository(package_repository.url, repo_path)


    
    return package_repository



def download_package_repository(url, path):
    # download the repository
    os.makedirs(path)
    git.Repo.clone_from(url, path)
