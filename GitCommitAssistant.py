import os
import subprocess
import datetime
import random
import shutil
import sys
import threading
import itertools
import time
import requests

def run_command(command, cwd=None, env=None, suppress_output=True):
    """
    Executes a shell command.
    """
    try:
        if suppress_output:
            subprocess.check_call(command, cwd=cwd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.check_call(command, cwd=cwd, env=env)
    except subprocess.CalledProcessError:
        print(f"\nError executing command: {' '.join(command)}")
        print("Please execute the above command manually in the terminal.")
        sys.exit(1)

def get_default_repo_names():
    """
    Returns a list of default repository names.
    """
    return [
        "api-service",
        "data-analysis-project",
        "web-scraper",
        "machine-learning-model",
        "automation-scripts",
        "data-visualization",
        "natural-language-processing",
        "image-processing-toolkit",
        "devops-automation",
        "backend-service"
    ]

def create_repo(repo_name, token):
    """
    Creates a GitHub repository using the GitHub API.
    """
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": repo_name,
        "auto_init": True,
        "private": False,
        "description": "Automated repository creation"
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"Repository '{repo_name}' created successfully.")
        return response.json()["clone_url"]
    elif response.status_code == 422:
        print(f"Repository '{repo_name}' already exists. Skipping creation.")
        return None
    else:
        print(f"Failed to create repository '{repo_name}'. Status Code: {response.status_code}")
        print("Response:", response.json())
        sys.exit(1)

def get_user_repos():
    """
    Prompts the user to input repository details or create new ones if none exist.
    """
    repos = {}
    has_repos = input("Do you have existing repositories? (y/n): ").strip().lower()
    if has_repos == 'y':
        try:
            num_repos = int(input("Enter the number of repositories: "))
        except ValueError:
            print("Invalid number. Please enter an integer.")
            sys.exit(1)
        for i in range(num_repos):
            name = input(f"Enter name for repository {i+1}: ").strip()
            url = input(f"Enter the GitHub URL for repository {i+1}: ").strip()
            use_default = input("Do you want to use default commit messages? (y/n): ").strip().lower()
            if use_default == 'y':
                repos[name] = {"url": url, "messages": None}
            else:
                messages = []
                print(f"Enter commit messages for {name} (type 'done' when finished):")
                while True:
                    msg = input()
                    if msg.lower() == 'done':
                        break
                    if msg.strip():
                        messages.append(msg.strip())
                if not messages:
                    print("No messages entered. Using default messages.")
                    repos[name] = {"url": url, "messages": None}
                else:
                    repos[name] = {"url": url, "messages": messages}
    else:
        token = input("Enter your GitHub Personal Access Token: ").strip()
        try:
            num_repos = int(input("Enter the number of repositories to create: "))
        except ValueError:
            print("Invalid number. Please enter an integer.")
            sys.exit(1)
        default_names = get_default_repo_names()
        for i in range(num_repos):
            name = input(f"Enter name for new repository {i+1} (leave blank for default): ").strip()
            if not name:
                if default_names:
                    name = default_names.pop(0)
                    print(f"Using default repository name: {name}")
                else:
                    print("No more default names available. Please enter a unique repository name.")
                    name = input(f"Enter name for new repository {i+1}: ").strip()
            clone_url = create_repo(name, token)
            if clone_url:
                repos[name] = {"url": clone_url, "messages": None}
        if not repos:
            print("No repositories to process.")
            sys.exit(0)
    return repos

def get_date_range():
    """
    Prompts the user to input the start and end dates.
    """
    try:
        start_date_str = input("Enter start date (YYYY-MM-DD): ").strip()
        end_date_str = input("Enter end date (YYYY-MM-DD): ").strip()
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        if start_date > end_date:
            print("Start date must be before end date.")
            sys.exit(1)
        return start_date, end_date
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        sys.exit(1)

def get_commit_range():
    """
    Prompts the user to input the minimum and maximum number of commits per day.
    """
    try:
        min_commits = int(input("Enter minimum number of commits per day: "))
        max_commits = int(input("Enter maximum number of commits per day: "))
        if min_commits < 1 or max_commits < min_commits:
            print("Invalid commit range.")
            sys.exit(1)
        return min_commits, max_commits
    except ValueError:
        print("Invalid input. Please enter integers.")
        sys.exit(1)

# Default commit messages
DEFAULT_COMMIT_MESSAGES = [
    "Initial commit",
    "Update README",
    "Fix bug",
    "Add feature",
    "Refactor code",
    "Improve performance",
    "Write tests",
    "Update dependencies",
    "Optimize algorithms",
    "Enhance documentation",
    "Fix typo",
    "Merge branch",
    "Remove unused code",
    "Implement authentication",
    "Add logging",
    "Configure CI/CD",
    "Update configuration",
    "Improve UI",
    "Fix security issue",
    "Add unit tests",
    "Update API endpoints",
    "Enhance error handling",
    "Optimize database queries",
    "Add support for new language",
    "Improve scalability",
    "Refactor modules",
    "Update license",
    "Add Docker support",
    "Improve caching",
    "Fix memory leak",
    "Enhance user experience"
]

def clone_repo(repo_name, repo_url, temp_dir):
    """
    Clones the repository to a temporary directory.
    """
    repo_path = os.path.join(temp_dir, repo_name)
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    run_command(["git", "clone", repo_url, repo_path])
    return repo_path

def make_commit(repo_path, commit_message, commit_date):
    """
    Creates a commit with the given message and date.
    """
    log_file = os.path.join(repo_path, "commit_log.txt")
    # Append commit message to the log file
    with open(log_file, "a") as f:
        f.write(f"{commit_date} - {commit_message}\n")
    run_command(["git", "add", "commit_log.txt"], cwd=repo_path)
    # Set commit date environment variables
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = commit_date.strftime("%Y-%m-%dT12:00:00")
    env["GIT_COMMITTER_DATE"] = commit_date.strftime("%Y-%m-%dT12:00:00")
    run_command(["git", "commit", "-m", commit_message], cwd=repo_path, env=env)

def push_changes(repo_path):
    """
    Pushes the committed changes to the remote repository.
    """
    try:
        run_command(["git", "push", "origin", "main"], cwd=repo_path)
    except:
        print(f"\nFailed to push changes for repository at {repo_path}.")
        print("Please navigate to the repository directory and push the changes manually:")
        print(f"cd {repo_path}")
        print("git push origin main")
        sys.exit(1)

def generate_commits(repos, start_date, end_date, min_commits, max_commits, temp_dir, spinner_event):
    """
    Generates commits for each repository within the specified date range.
    """
    for repo_name, repo_info in repos.items():
        print(f"\nProcessing repository: {repo_name}")
        repo_path = clone_repo(repo_name, repo_info["url"], temp_dir)
        messages = repo_info["messages"] if repo_info["messages"] else DEFAULT_COMMIT_MESSAGES
        current_date = start_date
        while current_date <= end_date:
            num_commits = random.randint(min_commits, max_commits)
            for _ in range(num_commits):
                message = random.choice(messages)
                make_commit(repo_path, message, current_date)
            current_date += datetime.timedelta(days=1)
        push_changes(repo_path)
        print(f"Completed processing for repository: {repo_name}")
    # Stop the spinner after all commits are done
    spinner_event.set()

def spinner(spinner_event):
    """
    Displays a spinning loader in green while processing.
    """
    spinner_chars = itertools.cycle(['|', '/', '-', '\\'])
    while not spinner_event.is_set():
        sys.stdout.write('\r\033[92m' + next(spinner_chars) + ' Processing...\033[0m')
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\r\033[92mDone!                \033[0m\n')

def main():
    """
    Main function to execute the script.
    """
    # Gather user inputs
    repos = get_user_repos()
    start_date, end_date = get_date_range()
    min_commits, max_commits = get_commit_range()
    
    # Create a temporary directory for cloning repositories
    temp_dir = "temp_repos"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    # Set up a spinner to indicate processing
    spinner_event = threading.Event()
    spinner_thread = threading.Thread(target=spinner, args=(spinner_event,))
    spinner_thread.start()
    
    # Generate commits
    generate_commits(repos, start_date, end_date, min_commits, max_commits, temp_dir, spinner_event)
    
    # Clean up the temporary directory
    shutil.rmtree(temp_dir)
    print("All repositories have been processed successfully.")

if __name__ == "__main__":
    main()
