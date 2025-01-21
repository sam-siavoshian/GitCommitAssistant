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
from concurrent.futures import ThreadPoolExecutor

def run_command(command, cwd=None, env=None, suppress_output=True):
    """
    Executes a shell command.
    
    Args:
        command (list): The command and its arguments to execute.
        cwd (str, optional): The working directory to execute the command in.
        env (dict, optional): Environment variables for the command.
        suppress_output (bool, optional): If True, suppresses the command's output.
    
    Raises:
        SystemExit: Exits the program if the command fails.
    """
    try:
        if suppress_output:
            subprocess.check_call(
                command, cwd=cwd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        else:
            subprocess.check_call(command, cwd=cwd, env=env)
    except subprocess.CalledProcessError:
        print(f"\nError executing command: {' '.join(command)}")
        print("Please execute the above command manually in the terminal.")
        sys.exit(1)

def get_default_repo_names(file_path='repo_names.txt'):
    """
    Loads repository names from a text file.
    
    Args:
        file_path (str): Path to the repository names file.
    
    Returns:
        list: A list of repository names.
    
    Raises:
        SystemExit: If the file does not exist or is empty.
    """
    if not os.path.exists(file_path):
        print(f"Repository names file '{file_path}' not found.")
        sys.exit(1)
    with open(file_path, 'r', encoding='utf-8') as f:
        names = [line.strip() for line in f if line.strip()]
    if not names:
        print(f"No repository names found in '{file_path}'. Please add repository names.")
        sys.exit(1)
    return names

def create_repo(repo_name, token):
    """
    Creates a GitHub repository using the GitHub API.
    
    Args:
        repo_name (str): The name of the repository to create.
        token (str): GitHub Personal Access Token for authentication.
    
    Returns:
        str or None: The clone URL if creation is successful, "exists" if repository already exists, or None on failure.
    """
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": repo_name,
        "auto_init": True,
        "private": True,
        "description": "Automated repository creation"
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"Repository '{repo_name}' created successfully.")
        return response.json()["clone_url"]
    elif response.status_code == 422:
        print(f"Repository '{repo_name}' already exists.")
        return "exists"
    else:
        print(f"Failed to create repository '{repo_name}'. Status Code: {response.status_code}")
        print("Response:", response.json())
        return None

def get_user_repos(repo_names):
    """
    Gathers repository information from the user, either existing repositories or creating new ones.
    
    Args:
        repo_names (list): List of default repository names.
    
    Returns:
        dict: A dictionary with repository names as keys and their details as values.
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
                print(f"Enter commit messages for '{name}' (type 'done' when finished):")
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
        for i in range(num_repos):
            while True:
                name = input(f"Enter name for new repository {i+1} (leave blank for default): ").strip()
                if not name:
                    if repo_names:
                        name = random.choice(repo_names)
                        repo_names.remove(name)
                        print(f"Using default repository name: {name}")
                    else:
                        print("No more default names available. Please enter a unique repository name.")
                        name = input(f"Enter name for new repository {i+1}: ").strip()
                clone_url = create_repo(name, token)
                if clone_url == "exists":
                    choice = input(f"Repository '{name}' already exists. Do you want to choose another name? (y/n): ").strip().lower()
                    if choice == 'y':
                        continue
                    else:
                        break
                elif clone_url:
                    repos[name] = {"url": clone_url, "messages": None}
                    break
                else:
                    sys.exit(1)
        if not repos:
            print("No repositories to process.")
            sys.exit(0)
    return repos

def get_date_range():
    """
    Prompts the user to input the start and end dates for commit generation.
    
    Returns:
        tuple: Start date and end date as datetime.date objects.
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
    
    Returns:
        tuple: Minimum and maximum number of commits per day as integers.
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

def get_commit_frequency():
    """
    Prompts the user to choose the frequency strategy for commits.
    
    Returns:
        dict: A dictionary containing the commit strategy and related parameters.
    """
    print("\nHow often should it make commits?")
    print("1. Every day")
    print("2. Randomly")
    print("3. Weekdays only")
    print("4. Weekends only")
    choice = input("Enter the number of your choice: ").strip()

    if choice == '1':
        print("\nYou have chosen to make commits every day.")
        try:
            commits_per_day = int(input("Enter the number of commits per day: "))
            if commits_per_day < 1:
                print("Number of commits must be at least 1.")
                sys.exit(1)
            return {
                'strategy': 'fixed',
                'min_commits': commits_per_day,
                'max_commits': commits_per_day,
                'days': 'all'
            }
        except ValueError:
            print("Invalid input. Please enter an integer.")
            sys.exit(1)

    elif choice == '2':
        print("\nYou have chosen to make commits randomly.")
        min_commits, max_commits = get_commit_range()
        return {
            'strategy': 'random',
            'min_commits': min_commits,
            'max_commits': max_commits,
            'days': 'all'
        }

    elif choice == '3':
        print("\nYou have chosen to make commits on weekdays only.")
        min_commits, max_commits = get_commit_range()
        return {
            'strategy': 'random',
            'min_commits': min_commits,
            'max_commits': max_commits,
            'days': 'weekdays'
        }

    elif choice == '4':
        print("\nYou have chosen to make commits on weekends only.")
        min_commits, max_commits = get_commit_range()
        return {
            'strategy': 'random',
            'min_commits': min_commits,
            'max_commits': max_commits,
            'days': 'weekends'
        }

    else:
        print("Invalid choice. Please enter a number between 1 and 4.")
        sys.exit(1)

def load_commit_messages(file_path='commit_messages.txt'):
    """
    Loads commit messages from a text file.
    
    Args:
        file_path (str): Path to the commit messages file.
    
    Returns:
        list: A list of commit messages.
    
    Raises:
        SystemExit: If the file does not exist or is empty.
    """
    if not os.path.exists(file_path):
        print(f"Commit messages file '{file_path}' not found.")
        sys.exit(1)
    with open(file_path, 'r', encoding='utf-8') as f:
        messages = [line.strip() for line in f if line.strip()]
    if not messages:
        print(f"No commit messages found in '{file_path}'. Please add commit messages.")
        sys.exit(1)
    return messages

def clone_repo(repo_name, repo_url, temp_dir):
    """
    Clones the specified repository into a temporary directory.
    
    Args:
        repo_name (str): The name of the repository.
        repo_url (str): The clone URL of the repository.
        temp_dir (str): The path to the temporary directory.
    
    Returns:
        str: The path to the cloned repository.
    """
    repo_path = os.path.join(temp_dir, repo_name)
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    run_command(["git", "clone", repo_url, repo_path])
    return repo_path

def make_commit(repo_path, commit_message, commit_date):
    """
    Creates a commit with the given message and date.
    
    Args:
        repo_path (str): The path to the cloned repository.
        commit_message (str): The commit message.
        commit_date (datetime.date): The date for the commit.
    """
    log_file = os.path.join(repo_path, "commit_log.txt")
    # Append commit message to the log file
    try:
        with open(log_file, "a") as f:
            f.write(f"{commit_date} - {commit_message}\n")
    except Exception as e:
        print(f"Error writing to commit_log.txt: {e}")
        sys.exit(1)
    # Stage the log file for commit
    run_command(["git", "add", "commit_log.txt"], cwd=repo_path)
    # Set commit date environment variables
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = commit_date.strftime("%Y-%m-%dT12:00:00")
    env["GIT_COMMITTER_DATE"] = commit_date.strftime("%Y-%m-%dT12:00:00")
    # Commit the changes
    run_command(["git", "commit", "-m", commit_message], cwd=repo_path, env=env)

def push_changes(repo_path):
    """
    Pushes the committed changes to the remote repository.
    
    Args:
        repo_path (str): The path to the cloned repository.
    
    Raises:
        SystemExit: If the push operation fails.
    """
    try:
        run_command(["git", "push", "origin", "main"], cwd=repo_path)
    except:
        print(f"\nFailed to push changes for repository at {repo_path}.")
        print("Please navigate to the repository directory and push the changes manually:")
        print(f"cd {repo_path}")
        print("git push origin main")
        sys.exit(1)

def generate_commits(repos, start_date, end_date, commit_frequency, temp_dir):
    """
    Generates commits for each repository within the specified date range based on commit frequency.
    
    Args:
        repos (dict): Dictionary containing repository details.
        start_date (datetime.date): The start date for commit generation.
        end_date (datetime.date): The end date for commit generation.
        commit_frequency (dict): Commit frequency strategy and parameters.
        temp_dir (str): Path to the temporary directory.
    """
    commit_messages = load_commit_messages()
    for repo_name, repo_info in repos.items():
        print(f"\nProcessing repository: {repo_name}")
        repo_path = clone_repo(repo_name, repo_info["url"], temp_dir)
        messages = repo_info["messages"] if repo_info["messages"] else commit_messages
        current_date = start_date

        while current_date <= end_date:
            # Determine if a commit should be made on this day based on the frequency strategy
            make_commit_today = False
            if commit_frequency['days'] == 'all':
                make_commit_today = True
            elif commit_frequency['days'] == 'weekdays' and current_date.weekday() < 5:
                make_commit_today = True
            elif commit_frequency['days'] == 'weekends' and current_date.weekday() >= 5:
                make_commit_today = True

            if make_commit_today:
                if commit_frequency['strategy'] == 'fixed':
                    num_commits = commit_frequency['min_commits']
                else:
                    num_commits = random.randint(commit_frequency['min_commits'], commit_frequency['max_commits'])
                for _ in range(num_commits):
                    message = random.choice(messages)
                    make_commit(repo_path, message, current_date)
            current_date += datetime.timedelta(days=1)

        push_changes(repo_path)
        print(f"Completed processing for repository: {repo_name}")

def spinner(spinner_event):
    """
    Displays a spinning loader in green while processing.
    
    Args:
        spinner_event (threading.Event): Event to signal the spinner to stop.
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
    # Load repository names from file
    repo_names = get_default_repo_names()
    # Gather repository information from the user
    repos = get_user_repos(repo_names)
    # Get the date range for commit generation
    start_date, end_date = get_date_range()
    # Get the commit frequency strategy and parameters
    commit_frequency = get_commit_frequency()

    # Create a temporary directory for cloning repositories
    temp_dir = "temp_repos"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Set up a spinner to indicate processing
    spinner_event = threading.Event()
    spinner_thread = threading.Thread(target=spinner, args=(spinner_event,))
    spinner_thread.start()

    # Generate commits for all repositories
    generate_commits(repos, start_date, end_date, commit_frequency, temp_dir)

    # Stop the spinner after all commits are done
    spinner_event.set()

    # Clean up the temporary directory
    try:
        shutil.rmtree(temp_dir)
    except PermissionError as e:
        print(f"PermissionError while deleting temp directory: {e}. Please delete '{temp_dir}' manually.")

    print("All repositories have been processed successfully.")

if __name__ == "__main__":
    main()
