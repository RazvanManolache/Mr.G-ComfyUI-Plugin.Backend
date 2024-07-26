# import os
# import git

# from .mrg_database import *

# # download or update package repository from github
# def update_package_repository(uuid):
#     package_repository = get_package_repository(uuid)
#     if package_repository is None:
#         return
#     if package_repository.system:
#         return
#     if package_repository.url == "":
#         return
   
#     # download or update package repository from github
#     # get the latest commit hash
#     latest_commit = get_latest_commit(package_repository.url)
#     if latest_commit is None:
#         return
#     if latest_commit == package_repository.commit:
#         return
#     # download the repository
#     download_package_repository(package_repository.url, package_repository.path)
#     # update the commit hash
#     update_package_repository_commit(uuid, latest_commit)

# def download_package_repository(url, path):
#     # download the repository
#     if os.path.exists(path):
#         shutil.rmtree(path)
#     os.makedirs(path)
#     git.Repo.clone_from(url, path)
    
