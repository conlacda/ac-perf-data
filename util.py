import subprocess
from os import getenv

def commit_to_github() -> None:
    if getenv("DEBUG") == '0':
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", "auto commit"])
        subprocess.run(["git", "push"])
