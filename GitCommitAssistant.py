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
    print("\nChoose date range for commits:")
    print("1. Last 30 days")
    print("2. Last 3 months")
    print("3. Last 6 months")
    print("4. Last year")
    print("5. Custom date range")
    
    choice = input("Enter your choice (1-5): ").strip()
    
    today = datetime.date.today()
    
    if choice == '1':
        start_date = today - datetime.timedelta(days=30)
        end_date = today
        print(f"Selected: Last 30 days ({start_date} to {end_date})")
    elif choice == '2':
        start_date = today - datetime.timedelta(days=90)
        end_date = today
        print(f"Selected: Last 3 months ({start_date} to {end_date})")
    elif choice == '3':
        start_date = today - datetime.timedelta(days=180)
        end_date = today
        print(f"Selected: Last 6 months ({start_date} to {end_date})")
    elif choice == '4':
        start_date = today - datetime.timedelta(days=365)
        end_date = today
        print(f"Selected: Last year ({start_date} to {end_date})")
    elif choice == '5':
        try:
            start_date_str = input("Enter start date (YYYY-MM-DD): ").strip()
            end_date_str = input("Enter end date (YYYY-MM-DD): ").strip()
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
            if start_date > end_date:
                print("Start date must be before end date.")
                sys.exit(1)
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            sys.exit(1)
    else:
        print("Invalid choice. Please enter a number between 1 and 5.")
        sys.exit(1)
    
    return start_date, end_date

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

def make_pr_commit(repo_path, commit_message, commit_date, file_name):
    """
    Creates a commit for a pull request with the given message and date.
    
    Args:
        repo_path (str): The path to the cloned repository.
        commit_message (str): The commit message.
        commit_date (datetime.date): The date for the commit.
        file_name (str): The name of the file to add.
    """
    # Stage the file for commit
    run_command(["git", "add", file_name], cwd=repo_path)
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

def get_pull_request_count():
    """
    Prompts the user to input the number of pull requests to create.
    
    Returns:
        int: Number of pull requests to create.
    """
    try:
        num_prs = int(input("Enter the number of pull requests to create: "))
        if num_prs < 1:
            print("Number of pull requests must be at least 1.")
            sys.exit(1)
        return num_prs
    except ValueError:
        print("Invalid input. Please enter an integer.")
        sys.exit(1)

def get_pr_date_range():
    """
    Prompts the user to input the start and end dates for pull request creation.
    
    Returns:
        tuple: Start date and end date as datetime.date objects.
    """
    print("\nChoose date range for pull requests:")
    print("1. Last 30 days")
    print("2. Last 3 months")
    print("3. Last 6 months")
    print("4. Last year")
    print("5. Custom date range")
    
    choice = input("Enter your choice (1-5): ").strip()
    
    today = datetime.date.today()
    
    if choice == '1':
        start_date = today - datetime.timedelta(days=30)
        end_date = today
        print(f"Selected: Last 30 days ({start_date} to {end_date})")
    elif choice == '2':
        start_date = today - datetime.timedelta(days=90)
        end_date = today
        print(f"Selected: Last 3 months ({start_date} to {end_date})")
    elif choice == '3':
        start_date = today - datetime.timedelta(days=180)
        end_date = today
        print(f"Selected: Last 6 months ({start_date} to {end_date})")
    elif choice == '4':
        start_date = today - datetime.timedelta(days=365)
        end_date = today
        print(f"Selected: Last year ({start_date} to {end_date})")
    elif choice == '5':
        try:
            start_date_str = input("Enter start date for PRs (YYYY-MM-DD): ").strip()
            end_date_str = input("Enter end date for PRs (YYYY-MM-DD): ").strip()
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
            if start_date > end_date:
                print("Start date must be before end date.")
                sys.exit(1)
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            sys.exit(1)
    else:
        print("Invalid choice. Please enter a number between 1 and 5.")
        sys.exit(1)
    
    return start_date, end_date

def create_branch(repo_path, branch_name):
    """
    Creates a new branch in the repository.
    
    Args:
        repo_path (str): The path to the cloned repository.
        branch_name (str): The name of the branch to create.
    """
    run_command(["git", "checkout", "-b", branch_name], cwd=repo_path)

def create_pull_request(repo_name, token, branch_name, title, body):
    """
    Creates a pull request using the GitHub API.
    
    Args:
        repo_name (str): The name of the repository.
        token (str): GitHub Personal Access Token for authentication.
        branch_name (str): The name of the branch to create the pull request from.
        title (str): The title of the pull request.
        body (str): The description of the pull request.
    
    Returns:
        int or None: The pull request number if created successfully, None otherwise.
    """
    # Get the username from the GitHub API
    user_url = "https://api.github.com/user"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    user_response = requests.get(user_url, headers=headers)
    if user_response.status_code != 200:
        print(f"Failed to get user information. Status Code: {user_response.status_code}")
        return None
    
    username = user_response.json()["login"]
    
    # Create the pull request
    pr_url = f"https://api.github.com/repos/{username}/{repo_name}/pulls"
    pr_data = {
        "title": title,
        "body": body,
        "head": branch_name,
        "base": "main"
    }
    
    pr_response = requests.post(pr_url, headers=headers, json=pr_data)
    if pr_response.status_code == 201:
        pr_number = pr_response.json()['number']
        print(f"Pull request #{pr_number} created successfully: {pr_response.json()['html_url']}")
        return pr_number
    else:
        print(f"Failed to create pull request. Status Code: {pr_response.status_code}")
        print("Response:", pr_response.json())
        return None

def merge_pull_request(repo_name, token, pr_number):
    """
    Merges a pull request using the GitHub API.
    
    Args:
        repo_name (str): The name of the repository.
        token (str): GitHub Personal Access Token for authentication.
        pr_number (int): The pull request number to merge.
    
    Returns:
        bool: True if the pull request was merged successfully, False otherwise.
    """
    # Get the username from the GitHub API
    user_url = "https://api.github.com/user"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    user_response = requests.get(user_url, headers=headers)
    if user_response.status_code != 200:
        return False
    
    username = user_response.json()["login"]
    
    # Merge the pull request
    merge_url = f"https://api.github.com/repos/{username}/{repo_name}/pulls/{pr_number}/merge"
    merge_data = {
        "commit_title": "Automated merge",
        "commit_message": "Merged by GitCommitAssistant",
        "merge_method": "merge"
    }
    
    merge_response = requests.put(merge_url, headers=headers, json=merge_data)
    if merge_response.status_code == 200:
        print(f"Pull request #{pr_number} merged successfully")
        return True
    else:
        print(f"Failed to merge pull request #{pr_number}")
        return False

def merge_pull_request_with_date(repo_name, token, pr_number, merge_date):
    """
    Attempts to merge a pull request and then update the merge commit date locally.
    
    Args:
        repo_name (str): The name of the repository.
        token (str): GitHub Personal Access Token for authentication.
        pr_number (int): The pull request number to merge.
        merge_date (datetime.date): The desired merge date.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    # First, try regular merge
    success = merge_pull_request(repo_name, token, pr_number)
    if not success:
        return False
    
    # Note: GitHub API doesn't allow setting merge commit dates directly
    # The commits within the PR will have the correct dates, which is what matters for activity
    return True

def create_and_merge_pr(repo_name, repo_path, token, commit_messages, pr_index, pr_date):
    """
    Creates a single pull request and merges it with proper backdating.
    
    Args:
        repo_name (str): The name of the repository.
        repo_path (str): The path to the cloned repository.
        token (str): GitHub Personal Access Token for authentication.
        commit_messages (list): List of commit messages to use.
        pr_index (int): The index of the PR being created.
        pr_date (datetime.date): The date for the PR.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Create a new branch
        branch_name = f"feature/automated-pr-{pr_index}-{random.randint(1000, 9999)}"
        create_branch(repo_path, branch_name)
        
        # Make multiple commits on the branch to simulate development over time
        # This helps with GitHub's activity tracking
        for i in range(random.randint(1, 3)):  # 1-3 commits per PR
            file_suffix = random.randint(100, 999)
            file_name = f"pr_feature_{pr_index}_{i+1}_{file_suffix}.txt"
            pr_file = os.path.join(repo_path, file_name)
            
            with open(pr_file, "w") as f:
                f.write(f"This is commit #{i+1} for automated pull request #{pr_index}.\n")
                f.write(f"Created at: {pr_date.isoformat()}\n")
                f.write(f"Feature description: {random.choice(commit_messages)}\n")
            
            # Commit with the specified date (slightly offset for multiple commits)
            commit_date = pr_date + datetime.timedelta(hours=i*2)  # Spread commits across the day
            commit_message = random.choice(commit_messages)
            make_pr_commit(repo_path, f"Add feature {pr_index} part {i+1}: {commit_message}", commit_date, file_name)
        
        # Push the branch
        run_command(["git", "push", "-u", "origin", branch_name], cwd=repo_path)
        
        # Create the pull request
        pr_title = f"Feature {pr_index}: {random.choice(commit_messages)}"
        pr_body = f"This pull request adds feature {pr_index}.\n\nImplemented on {pr_date.strftime('%Y-%m-%d')}\n\n{random.choice(commit_messages)}"
        pr_number = create_pull_request(repo_name, token, branch_name, pr_title, pr_body)
        
        # If PR was created successfully, merge it immediately
        if pr_number:
            # Create a merge commit with the correct date
            merge_success = merge_pull_request_with_date(repo_name, token, pr_number, pr_date)
            if not merge_success:
                # Fallback to regular merge if date-specific merge fails
                merge_pull_request(repo_name, token, pr_number)
            
        # Switch back to main branch for the next PR
        run_command(["git", "checkout", "main"], cwd=repo_path)
        
        return True
    except Exception as e:
        print(f"Error creating PR {pr_index}: {e}")
        return False

def generate_pull_requests(repos, num_prs, start_date, end_date, temp_dir, token):
    """
    Generates pull requests for each repository across the specified date range.
    This approach creates commits on historical dates and pushes them individually.
    
    Args:
        repos (dict): Dictionary containing repository details.
        num_prs (int): Number of pull requests to create per repository.
        start_date (datetime.date): The start date for PR creation.
        end_date (datetime.date): The end date for PR creation.
        temp_dir (str): Path to the temporary directory.
        token (str): GitHub Personal Access Token for authentication.
    """
    print(f"\n🚀 Creating {num_prs} pull requests from {start_date} to {end_date}")
    print("⚠️  Note: This will create commits on historical dates for proper GitHub activity tracking")
    
    # Load commit messages to use as PR titles and descriptions
    commit_messages = load_commit_messages()
    
    # Calculate date distribution for PRs
    total_days = (end_date - start_date).days + 1
    
    for repo_name, repo_info in repos.items():
        print(f"\nProcessing repository: {repo_name}")
        repo_path = clone_repo(repo_name, repo_info["url"], temp_dir)
        
        # Group PRs by date for better GitHub activity distribution
        date_groups = {}
        for i in range(num_prs):
            if total_days >= num_prs:
                day_offset = (i * total_days) // num_prs
            else:
                day_offset = random.randint(0, total_days - 1)
            pr_date = start_date + datetime.timedelta(days=day_offset)
            
            if pr_date not in date_groups:
                date_groups[pr_date] = []
            date_groups[pr_date].append(i + 1)
        
        # Process PRs grouped by date
        for pr_date, pr_indices in sorted(date_groups.items()):
            print(f"Creating {len(pr_indices)} PRs for {pr_date}")
            
            for pr_index in pr_indices:
                success = create_historical_pr(repo_name, repo_path, token, commit_messages, pr_index, pr_date)
                if not success:
                    print(f"Failed to create PR {pr_index} for {repo_name}")
        
        print(f"Completed processing pull requests for repository: {repo_name}")

def create_historical_pr(repo_name, repo_path, token, commit_messages, pr_index, pr_date):
    """
    Creates a pull request with commits that have historical dates.
    Uses a different approach to ensure GitHub recognizes the historical activity.
    
    Args:
        repo_name (str): The name of the repository.
        repo_path (str): The path to the cloned repository.
        token (str): GitHub Personal Access Token for authentication.
        commit_messages (list): List of commit messages to use.
        pr_index (int): The index of the PR being created.
        pr_date (datetime.date): The date for the PR.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Create a new branch
        branch_name = f"feature/historical-pr-{pr_index}-{pr_date.strftime('%Y%m%d')}"
        create_branch(repo_path, branch_name)
        
        # Create multiple commits with the historical date
        num_commits = random.randint(1, 3)
        for i in range(num_commits):
            file_suffix = random.randint(100, 999)
            file_name = f"historical_feature_{pr_index}_{i+1}_{file_suffix}.txt"
            pr_file = os.path.join(repo_path, file_name)
            
            # Create file content
            with open(pr_file, "w") as f:
                f.write(f"Historical PR #{pr_index} - Commit {i+1}\n")
                f.write(f"Date: {pr_date.isoformat()}\n")
                f.write(f"Feature: {random.choice(commit_messages)}\n")
                f.write(f"Timestamp: {pr_date.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Create commit with historical date
            commit_time = pr_date + datetime.timedelta(hours=i*3, minutes=random.randint(0, 59))
            commit_message = f"Add historical feature {pr_index}.{i+1}: {random.choice(commit_messages)}"
            
            # Stage the file
            run_command(["git", "add", file_name], cwd=repo_path)
            
            # Create commit with historical date
            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = commit_time.strftime("%Y-%m-%dT%H:%M:%S")
            env["GIT_COMMITTER_DATE"] = commit_time.strftime("%Y-%m-%dT%H:%M:%S")
            
            run_command(["git", "commit", "-m", commit_message], cwd=repo_path, env=env)
        
        # Push the branch with historical commits
        run_command(["git", "push", "-u", "origin", branch_name], cwd=repo_path)
        
        # Create the pull request
        pr_title = f"Historical Feature {pr_index}: {random.choice(commit_messages)}"
        pr_body = f"This pull request implements feature {pr_index}.\n\nDeveloped on: {pr_date.strftime('%Y-%m-%d')}\n\n{random.choice(commit_messages)}"
        pr_number = create_pull_request(repo_name, token, branch_name, pr_title, pr_body)
        
        # Merge the PR immediately
        if pr_number:
            merge_pull_request(repo_name, token, pr_number)
        
        # Switch back to main branch
        run_command(["git", "checkout", "main"], cwd=repo_path)
        
        return True
        
    except Exception as e:
        print(f"Error creating historical PR {pr_index}: {e}")
        return False

def prepare_commit_data(commit_date, commit_index, commit_messages):
    """
    Prepares commit data without touching the git repository (thread-safe).
    
    Args:
        commit_date (datetime.date): The date for the commit.
        commit_index (int): The index of this commit.
        commit_messages (list): List of commit messages to choose from.
    
    Returns:
        dict: Commit data including file info, timestamp, and message.
    """
    # Create unique file for this commit
    timestamp = datetime.datetime.combine(commit_date, datetime.time(
        hour=random.randint(9, 17),
        minute=random.randint(0, 59),
        second=random.randint(0, 59)
    ))
    
    file_name = f"pr_commit_{commit_date.strftime('%Y%m%d')}_{commit_index}_{random.randint(1000, 9999)}.txt"
    
    # Prepare file content
    file_content = f"Historical commit #{commit_index} for PR simulation\n"
    file_content += f"Date: {commit_date.isoformat()}\n"
    file_content += f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
    file_content += f"Feature: {random.choice(commit_messages)}\n"
    
    commit_message = f"Historical commit {commit_index}: {random.choice(commit_messages)}"
    
    return {
        'file_name': file_name,
        'file_content': file_content,
        'timestamp': timestamp,
        'commit_message': commit_message,
        'commit_date': commit_date,
        'commit_index': commit_index
    }

def create_historical_commit_from_data(repo_path, commit_data):
    """
    Creates a commit from prepared data (not thread-safe, must be called sequentially).
    
    Args:
        repo_path (str): The path to the repository.
        commit_data (dict): Prepared commit data.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        file_path = os.path.join(repo_path, commit_data['file_name'])
        
        # Create file
        with open(file_path, "w") as f:
            f.write(commit_data['file_content'])
        
        # Stage the file
        run_command(["git", "add", commit_data['file_name']], cwd=repo_path)
        
        # Create commit with historical timestamp
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = commit_data['timestamp'].strftime("%Y-%m-%dT%H:%M:%S")
        env["GIT_COMMITTER_DATE"] = commit_data['timestamp'].strftime("%Y-%m-%dT%H:%M:%S")
        
        run_command(["git", "commit", "-m", commit_data['commit_message']], cwd=repo_path, env=env)
        
        return True
    except Exception as e:
        print(f"Error creating commit {commit_data['commit_index']}: {e}")
        return False

def generate_historical_commits_for_prs(repos, num_prs, start_date, end_date, temp_dir):
    """
    Generates commits with historical dates using parallel processing for maximum speed.
    This is the correct approach for backdating GitHub activity.
    
    Args:
        repos (dict): Dictionary containing repository details.
        num_prs (int): Number of pull requests worth of commits to create.
        start_date (datetime.date): The start date for PR creation.
        end_date (datetime.date): The end date for PR creation.
        temp_dir (str): Path to the temporary directory.
    """
    print(f"\n🚀 Creating historical commits for {num_prs} PRs from {start_date} to {end_date}")
    print("⚡ Using parallel processing for maximum speed (10 concurrent operations)")
    print("✅ This approach creates commits with historical dates that GitHub will recognize")
    
    # Load commit messages
    commit_messages = load_commit_messages()
    
    # Calculate date distribution
    total_days = (end_date - start_date).days + 1
    
    for repo_name, repo_info in repos.items():
        print(f"\nProcessing repository: {repo_name}")
        repo_path = clone_repo(repo_name, repo_info["url"], temp_dir)
        
        # Create a list of all commits to be made
        all_commits = []
        for i in range(num_prs):
            if total_days >= num_prs:
                day_offset = (i * total_days) // num_prs
            else:
                day_offset = random.randint(0, total_days - 1)
            commit_date = start_date + datetime.timedelta(days=day_offset)
            
            # Each PR gets 1-3 commits
            commits_per_pr = random.randint(1, 3)
            for j in range(commits_per_pr):
                all_commits.append((commit_date, len(all_commits) + 1))
        
        print(f"Creating {len(all_commits)} total commits with optimized parallel processing...")
        
        # Step 1: Prepare all commit data in parallel (thread-safe)
        print("📋 Preparing commit data in parallel...")
        all_commit_data = []
        
        batch_size = 50  # Larger batches for data preparation
        total_batches = (len(all_commits) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(all_commits))
            batch_commits = all_commits[start_idx:end_idx]
            
            # Prepare commit data in parallel
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for commit_date, commit_index in batch_commits:
                    future = executor.submit(prepare_commit_data, commit_date, commit_index, commit_messages)
                    futures.append(future)
                
                # Collect all prepared data
                for future in futures:
                    commit_data = future.result()
                    if commit_data:
                        all_commit_data.append(commit_data)
            
            print(f"✅ Prepared batch {batch_num + 1}/{total_batches}")
        
        # Step 2: Create commits sequentially (git operations must be sequential)
        print(f"🚀 Creating {len(all_commit_data)} commits sequentially...")
        successful_commits = 0
        
        for i, commit_data in enumerate(all_commit_data, 1):
            if create_historical_commit_from_data(repo_path, commit_data):
                successful_commits += 1
            
            # Progress update every 100 commits
            if i % 100 == 0 or i == len(all_commit_data):
                print(f"Progress: {i}/{len(all_commit_data)} commits created ({successful_commits} successful)")
        
        print(f"✅ All commits completed: {successful_commits}/{len(all_commit_data)} successful")
        
        # Push all historical commits at once
        print(f"Pushing all {len(all_commits)} historical commits for {repo_name}...")
        push_changes(repo_path)
        
        print(f"✅ Completed historical commits for repository: {repo_name}")
        print(f"🎯 Total commits created: {len(all_commits)}")

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
    print("\nWelcome to GitCommitAssistant!")
    print("What would you like to do?")
    print("1. Generate commits")
    print("2. Create actual pull requests (will increase PR count in activity chart)")
    print("3. Create discussions with accepted answers (for Galaxy Brain achievement)")
    print("4. Create coauthored pull requests (for Pair Extraordinaire achievement)")
    
    choice = input("Enter your choice (1, 2, 3, or 4): ").strip()
    
    if choice not in ['1', '2', '3', '4']:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")
        sys.exit(1)
    
    # Load repository names from file
    repo_names = get_default_repo_names()
    
    # Gather repository information from the user
    repos = get_user_repos(repo_names)
    
    # Get all required inputs before starting the spinner
    if choice == '1':
        # Generate commits - get date range and frequency
        start_date, end_date = get_date_range()
        commit_frequency = get_commit_frequency()
        token = None
        num_prs = None
        num_discussions = None
    elif choice == '2':
        # Create actual pull requests with historical commits - get PR count, date range, and token
        num_prs = get_pull_request_count()
        start_date, end_date = get_pr_date_range()
        token = input("Enter your GitHub Personal Access Token: ").strip()
        commit_frequency = None
        num_discussions = None
    elif choice == '3':
        # Create discussions with accepted answers - get discussion count and token
        num_discussions = get_discussion_count()
        token = input("Enter your GitHub Personal Access Token: ").strip()
        start_date = None
        end_date = None
        commit_frequency = None
        num_prs = None
    else:  # choice == '4'
        # Create coauthored pull requests - get PR count, date range, coauthors, and token
        num_prs = get_coauthored_pull_request_count()
        start_date, end_date = get_coauthored_pull_request_date_range()
        coauthors = get_coauthor_information()
        token = input("Enter your GitHub Personal Access Token: ").strip()
        commit_frequency = None
        num_discussions = None

    # Create a temporary directory for cloning repositories (only needed for commits and PRs)
    temp_dir = "temp_repos"
    if choice in ['1', '2', '4']:
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

    # Set up a spinner to indicate processing
    spinner_event = threading.Event()
    spinner_thread = threading.Thread(target=spinner, args=(spinner_event,))
    spinner_thread.start()

    if choice == '1':
        # Generate commits
        generate_commits(repos, start_date, end_date, commit_frequency, temp_dir)
    elif choice == '2':
        # Create actual pull requests with historical commits
        generate_actual_historical_prs(repos, num_prs, start_date, end_date, temp_dir, token)
    elif choice == '3':
        # Create discussions with accepted answers
        generate_discussions(repos, num_discussions, temp_dir, token)
    else:  # choice == '4'
        # Create coauthored pull requests
        generate_coauthored_pull_requests(repos, num_prs, start_date, end_date, temp_dir, token, coauthors)

    # Stop the spinner after all operations are done
    spinner_event.set()

    # Clean up the temporary directory (only if it was created)
    if choice in ['1', '2', '4']:
        try:
            shutil.rmtree(temp_dir)
        except PermissionError as e:
            print(f"PermissionError while deleting temp directory: {e}. Please delete '{temp_dir}' manually.")

    print("All operations have been completed successfully.")

def generate_actual_historical_prs(repos, num_prs, start_date, end_date, temp_dir, token):
    """
    Creates actual pull requests with historical commits that will show up in GitHub's activity chart.
    This approach creates real PRs that get merged, which is what GitHub counts.
    
    Args:
        repos (dict): Dictionary containing repository details.
        num_prs (int): Number of pull requests to create.
        start_date (datetime.date): The start date for PR creation.
        end_date (datetime.date): The end date for PR creation.
        temp_dir (str): Path to the temporary directory.
        token (str): GitHub Personal Access Token for authentication.
    """
    print(f"\n🚀 Creating {num_prs} ACTUAL pull requests from {start_date} to {end_date}")
    print("✅ This creates real PRs that will count in your GitHub activity chart")
    
    # Load commit messages
    commit_messages = load_commit_messages()
    
    # Calculate date distribution
    total_days = (end_date - start_date).days + 1
    
    for repo_name, repo_info in repos.items():
        print(f"\nProcessing repository: {repo_name}")
        repo_path = clone_repo(repo_name, repo_info["url"], temp_dir)
        
        # Distribute PRs across the date range
        pr_dates = []
        for i in range(num_prs):
            if total_days >= num_prs:
                day_offset = (i * total_days) // num_prs
            else:
                day_offset = random.randint(0, total_days - 1)
            pr_date = start_date + datetime.timedelta(days=day_offset)
            pr_dates.append(pr_date)
        
        # Create PRs in batches to manage API rate limits
        batch_size = 20  # Smaller batches for API calls
        total_batches = (len(pr_dates) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(pr_dates))
            batch_dates = pr_dates[start_idx:end_idx]
            
            print(f"Creating batch {batch_num + 1}/{total_batches} ({len(batch_dates)} PRs)")
            
            for i, pr_date in enumerate(batch_dates):
                pr_index = start_idx + i + 1
                success = create_single_historical_pr(repo_name, repo_path, token, commit_messages, pr_index, pr_date)
                if success:
                    print(f"✅ PR {pr_index}/{num_prs} created and merged for {pr_date}")
                else:
                    print(f"❌ Failed to create PR {pr_index}")
                
                # Small delay to avoid API rate limits
                time.sleep(0.5)
        
        print(f"✅ Completed {num_prs} pull requests for repository: {repo_name}")

def create_single_historical_pr(repo_name, repo_path, token, commit_messages, pr_index, pr_date):
    """
    Creates a single pull request with historical commits.
    
    Args:
        repo_name (str): The name of the repository.
        repo_path (str): The path to the cloned repository.
        token (str): GitHub Personal Access Token for authentication.
        commit_messages (list): List of commit messages to use.
        pr_index (int): The index of the PR being created.
        pr_date (datetime.date): The date for the PR.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Create a new branch
        branch_name = f"feature/historical-pr-{pr_index}-{pr_date.strftime('%Y%m%d')}-{random.randint(100, 999)}"
        create_branch(repo_path, branch_name)
        
        # Create 1-3 commits with historical dates
        num_commits = random.randint(1, 3)
        for commit_num in range(num_commits):
            # Create unique file
            timestamp = datetime.datetime.combine(pr_date, datetime.time(
                hour=random.randint(9, 17),
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )) + datetime.timedelta(hours=commit_num * 2)
            
            file_name = f"historical_pr_{pr_index}_{commit_num + 1}_{random.randint(1000, 9999)}.txt"
            file_path = os.path.join(repo_path, file_name)
            
            # Create file content
            with open(file_path, "w") as f:
                f.write(f"Historical Pull Request #{pr_index} - Commit {commit_num + 1}\n")
                f.write(f"Date: {pr_date.isoformat()}\n")
                f.write(f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Feature: {random.choice(commit_messages)}\n")
                f.write(f"Branch: {branch_name}\n")
            
            # Stage and commit with historical date
            run_command(["git", "add", file_name], cwd=repo_path)
            
            commit_message = f"Add feature {pr_index}.{commit_num + 1}: {random.choice(commit_messages)}"
            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = timestamp.strftime("%Y-%m-%dT%H:%M:%S")
            env["GIT_COMMITTER_DATE"] = timestamp.strftime("%Y-%m-%dT%H:%M:%S")
            
            run_command(["git", "commit", "-m", commit_message], cwd=repo_path, env=env)
        
        # Push the branch
        run_command(["git", "push", "-u", "origin", branch_name], cwd=repo_path)
        
        # Create the pull request
        pr_title = f"Historical Feature {pr_index}: {random.choice(commit_messages)}"
        pr_body = f"This pull request implements feature {pr_index}.\n\nDeveloped on: {pr_date.strftime('%Y-%m-%d')}\n\nFeatures:\n"
        for i in range(num_commits):
            pr_body += f"- {random.choice(commit_messages)}\n"
        
        pr_number = create_pull_request(repo_name, token, branch_name, pr_title, pr_body)
        
        if pr_number:
            # Merge the PR immediately
            merge_success = merge_pull_request(repo_name, token, pr_number)
            if merge_success:
                # Switch back to main branch
                run_command(["git", "checkout", "main"], cwd=repo_path)
                return True
        
        return False
        
    except Exception as e:
        print(f"Error creating historical PR {pr_index}: {e}")
        # Try to switch back to main branch even if there was an error
        try:
            run_command(["git", "checkout", "main"], cwd=repo_path)
        except:
            pass
        return False

def get_discussion_count():
    """
    Prompts the user to input the number of discussions to create.
    
    Returns:
        int: Number of discussions to create.
    """
    try:
        num_discussions = int(input("Enter the number of discussions to create: "))
        if num_discussions < 1:
            print("Number of discussions must be at least 1.")
            sys.exit(1)
        return num_discussions
    except ValueError:
        print("Invalid input. Please enter an integer.")
        sys.exit(1)

def create_discussion(repo_name, token, title, body, category="General"):
    """
    Creates a GitHub Discussion using the GitHub API.
    
    Args:
        repo_name (str): The name of the repository.
        token (str): GitHub Personal Access Token for authentication.
        title (str): The title of the discussion.
        body (str): The body content of the discussion.
        category (str): The discussion category.
    
    Returns:
        str or None: The discussion number if creation is successful, None otherwise.
    """
    # First, get the repository ID and category ID
    repo_query = """
    query($owner: String!, $name: String!) {
        repository(owner: $owner, name: $name) {
            id
            discussionCategories(first: 10) {
                nodes {
                    id
                    name
                    description
                    isAnswerable
                }
            }
        }
    }
    """
    
    # Extract owner and repo name from repo_name
    if '/' in repo_name:
        owner, name = repo_name.split('/', 1)
    else:
        # Get current user as owner
        user_response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"}
        )
        if user_response.status_code == 200:
            owner = user_response.json()["login"]
            name = repo_name
        else:
            print(f"Failed to get user info. Status Code: {user_response.status_code}")
            return None
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Get repository and category info
    repo_variables = {"owner": owner, "name": name}
    repo_response = requests.post(
        "https://api.github.com/graphql",
        headers=headers,
        json={"query": repo_query, "variables": repo_variables}
    )
    
    if repo_response.status_code != 200:
        print(f"Failed to get repository info. Status Code: {repo_response.status_code}")
        return None
    
    repo_data = repo_response.json()
    if "errors" in repo_data:
        print(f"GraphQL errors: {repo_data['errors']}")
        return None
    
    repository = repo_data["data"]["repository"]
    repo_id = repository["id"]
    
    # Find the category ID (prioritize categories that support answers)
    category_id = None
    answerable_category_id = None
    
    for cat in repository["discussionCategories"]["nodes"]:
        # Look for answerable categories first
        if cat.get("isAnswerable", False):
            answerable_category_id = cat["id"]
            print(f"Found answerable category: {cat['name']}")
            break
        # Fallback to requested category
        elif cat["name"].lower() == category.lower():
            category_id = cat["id"]
    
    # Prefer answerable category if available, otherwise use requested category
    if answerable_category_id:
        category_id = answerable_category_id
        print(f"Using answerable category for discussion (supports marking answers)")
    elif category_id:
        print(f"Using {category} category for discussion")
    elif repository["discussionCategories"]["nodes"]:
        # Last resort: use first available category
        category_id = repository["discussionCategories"]["nodes"][0]["id"]
        print(f"Using {repository['discussionCategories']['nodes'][0]['name']} category (may not support answers)")
        print(f"⚠️  This category may not support marking answers - discussions will be created but answers won't be marked")
    
    if not category_id:
        print("No discussion categories available in this repository.")
        print("📋 To enable GitHub Discussions:")
        print("   1. Go to your repository on GitHub")
        print("   2. Click 'Settings' tab")
        print("   3. Scroll to 'Features' section")
        print("   4. Check the 'Discussions' checkbox")
        print("   5. Click 'Set up discussions'")
        print("   This will create the default discussion categories needed for this feature.")
        return None
    
    # Create the discussion
    create_query = """
    mutation($repositoryId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
        createDiscussion(input: {repositoryId: $repositoryId, categoryId: $categoryId, title: $title, body: $body}) {
            discussion {
                number
                id
            }
        }
    }
    """
    
    create_variables = {
        "repositoryId": repo_id,
        "categoryId": category_id,
        "title": title,
        "body": body
    }
    
    create_response = requests.post(
        "https://api.github.com/graphql",
        headers=headers,
        json={"query": create_query, "variables": create_variables}
    )
    
    if create_response.status_code == 200:
        create_data = create_response.json()
        if "errors" in create_data:
            print(f"Failed to create discussion. Errors: {create_data['errors']}")
            return None
        
        discussion = create_data["data"]["createDiscussion"]["discussion"]
        print(f"Discussion #{discussion['number']} created successfully: {title}")
        return discussion["number"], discussion["id"]
    else:
        print(f"Failed to create discussion. Status Code: {create_response.status_code}")
        return None

def add_discussion_comment(repo_name, token, discussion_id, comment_body):
    """
    Adds a comment to a GitHub Discussion.
    
    Args:
        repo_name (str): The name of the repository.
        token (str): GitHub Personal Access Token for authentication.
        discussion_id (str): The ID of the discussion.
        comment_body (str): The body content of the comment.
    
    Returns:
        str or None: The comment ID if successful, None otherwise.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    comment_query = """
    mutation($discussionId: ID!, $body: String!) {
        addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
            comment {
                id
            }
        }
    }
    """
    
    comment_variables = {
        "discussionId": discussion_id,
        "body": comment_body
    }
    
    comment_response = requests.post(
        "https://api.github.com/graphql",
        headers=headers,
        json={"query": comment_query, "variables": comment_variables}
    )
    
    if comment_response.status_code == 200:
        comment_data = comment_response.json()
        if "errors" in comment_data:
            print(f"Failed to add comment. Errors: {comment_data['errors']}")
            return None
        
        comment_id = comment_data["data"]["addDiscussionComment"]["comment"]["id"]
        print("Comment added successfully")
        return comment_id
    else:
        print(f"Failed to add comment. Status Code: {comment_response.status_code}")
        return None

def mark_discussion_answer(repo_name, token, comment_id):
    """
    Marks a discussion comment as the accepted answer.
    
    Args:
        repo_name (str): The name of the repository.
        token (str): GitHub Personal Access Token for authentication.
        comment_id (str): The ID of the comment to mark as answer.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    answer_query = """
    mutation($id: ID!) {
        markDiscussionCommentAsAnswer(input: {id: $id}) {
            discussion {
                id
            }
        }
    }
    """
    
    answer_variables = {"id": comment_id}
    
    answer_response = requests.post(
        "https://api.github.com/graphql",
        headers=headers,
        json={"query": answer_query, "variables": answer_variables}
    )
    
    if answer_response.status_code == 200:
        answer_data = answer_response.json()
        if "errors" in answer_data:
            print(f"Failed to mark as answer. Errors: {answer_data['errors']}")
            return False
        
        print("Comment marked as accepted answer ✅")
        return True
    else:
        print(f"Failed to mark as answer. Status Code: {answer_response.status_code}")
        return False

def generate_discussion_content():
    """
    Generates realistic discussion topics and answers for development-related discussions.
    
    Returns:
        tuple: (title, question_body, answer_body)
    """
    topics = [
        {
            "title": "How to optimize database queries in Python?",
            "question": "I'm working on a Python application that makes frequent database queries, and I'm noticing performance issues. What are some best practices for optimizing database queries in Python?\n\nI'm currently using SQLAlchemy with PostgreSQL. The queries are taking too long, especially when dealing with large datasets.",
            "answer": "Great question! Here are several strategies to optimize database queries in Python:\n\n1. **Use indexes effectively** - Make sure your frequently queried columns have proper indexes\n2. **Lazy loading vs Eager loading** - Use `joinedload()` or `selectinload()` to avoid N+1 query problems\n3. **Query optimization** - Use `query.options()` to control what gets loaded\n4. **Connection pooling** - Configure proper connection pooling to reduce connection overhead\n5. **Raw SQL for complex queries** - Sometimes raw SQL performs better than ORM for complex operations\n\nHere's an example with SQLAlchemy:\n```python\n# Instead of this (N+1 problem)\nusers = session.query(User).all()\nfor user in users:\n    print(user.posts)  # This triggers additional queries\n\n# Do this (eager loading)\nusers = session.query(User).options(joinedload(User.posts)).all()\n```\n\nAlso consider using database-specific features like PostgreSQL's `EXPLAIN ANALYZE` to understand query execution plans."
        },
        {
            "title": "Best practices for API error handling in REST services?",
            "question": "I'm building a REST API and want to implement proper error handling. What are the industry best practices for handling and returning errors in REST APIs?\n\nShould I always return JSON error responses? How detailed should error messages be?",
            "answer": "Excellent question! Here are the key best practices for REST API error handling:\n\n## HTTP Status Codes\n- Use appropriate HTTP status codes (400 for client errors, 500 for server errors)\n- Be consistent across your API\n\n## Error Response Format\nUse a consistent JSON structure:\n```json\n{\n  \"error\": {\n    \"code\": \"VALIDATION_ERROR\",\n    \"message\": \"Invalid input provided\",\n    \"details\": [\n      {\n        \"field\": \"email\",\n        \"message\": \"Email format is invalid\"\n      }\n    ]\n  }\n}\n```\n\n## Security Considerations\n- Don't expose sensitive information in error messages\n- Log detailed errors server-side, return generic messages to clients\n- Use error codes instead of exposing internal error details\n\n## Implementation Tips\n- Create custom exception classes for different error types\n- Use middleware/decorators for consistent error handling\n- Include request IDs for debugging\n- Provide helpful error messages that guide users toward solutions"
        },
        {
            "title": "Docker container memory optimization strategies?",
            "question": "My Docker containers are consuming more memory than expected in production. What are some effective strategies to optimize memory usage in Docker containers?\n\nI'm running a Node.js application with Redis and PostgreSQL in separate containers.",
            "answer": "Memory optimization in Docker is crucial for production deployments. Here are proven strategies:\n\n## Container-Level Optimization\n\n1. **Set memory limits**:\n```bash\ndocker run -m 512m your-app\n# or in docker-compose.yml\nservices:\n  app:\n    mem_limit: 512m\n```\n\n2. **Use multi-stage builds** to reduce image size:\n```dockerfile\n# Build stage\nFROM node:16 AS builder\nWORKDY /app\nCOPY package*.json ./\nRUN npm ci --only=production\n\n# Runtime stage\nFROM node:16-alpine\nWORKDY /app\nCOPY --from=builder /app/node_modules ./node_modules\nCOPY . .\n```\n\n## Application-Level Optimization\n\n**For Node.js:**\n- Set `--max-old-space-size` flag\n- Use streaming for large data processing\n- Implement proper connection pooling\n\n**For Redis:**\n- Configure `maxmemory` and `maxmemory-policy`\n- Use appropriate data structures\n- Enable memory optimization settings\n\n**For PostgreSQL:**\n- Tune `shared_buffers`, `work_mem`, and `maintenance_work_mem`\n- Use connection pooling (pgbouncer)\n\n## Monitoring\n- Use `docker stats` to monitor real-time usage\n- Implement health checks\n- Set up alerts for memory thresholds\n\nThese optimizations typically reduce memory usage by 30-50% in production environments."
        },
        {
            "title": "Git workflow for large development teams?",
            "question": "Our development team is growing (15+ developers) and our current Git workflow is becoming chaotic. What Git workflow would you recommend for large teams to maintain code quality and avoid conflicts?",
            "answer": "For large teams, I recommend the **GitFlow workflow** with some modern adaptations. Here's a comprehensive approach:\n\n## Branch Strategy\n\n```\nmain (production-ready code)\n├── develop (integration branch)\n├── feature/* (individual features)\n├── release/* (release preparation)\n└── hotfix/* (emergency fixes)\n```\n\n## Workflow Process\n\n1. **Feature Development**:\n   - Create feature branches from `develop`\n   - Use descriptive names: `feature/user-authentication`\n   - Keep features small and focused\n\n2. **Code Review Process**:\n   - Require pull request reviews (minimum 2 reviewers)\n   - Use automated CI/CD checks\n   - Implement branch protection rules\n\n3. **Integration**:\n   - Merge features to `develop` via PR\n   - Regular integration testing on `develop`\n   - Create release branches for final testing\n\n## Best Practices for Large Teams\n\n- **Conventional Commits**: Use standardized commit messages\n- **Rebase vs Merge**: Use rebase for feature branches, merge for integration\n- **Protected Branches**: Protect `main` and `develop` branches\n- **Automated Testing**: Run tests on every PR\n- **Release Notes**: Auto-generate from commit messages\n\n## Tools & Configuration\n\n```bash\n# Set up branch protection\ngh api repos/:owner/:repo/branches/main/protection \\\n  --method PUT \\\n  --field required_status_checks='{}' \\\n  --field enforce_admins=true\n```\n\nThis workflow scales well and maintains code quality while allowing parallel development across large teams."
        },
        {
            "title": "Microservices communication patterns - which to choose?",
            "question": "I'm designing a microservices architecture and need to decide on communication patterns. Should I use synchronous (REST/gRPC) or asynchronous (message queues) communication between services?\n\nThe system will handle e-commerce transactions with inventory, payments, and notifications.",
            "answer": "Great architectural question! The choice depends on your specific use case. For e-commerce, I recommend a **hybrid approach**:\n\n## Synchronous Communication (REST/gRPC)\n\n**Use for:**\n- Real-time data queries (product catalog, user profiles)\n- Immediate validation (inventory checks, payment authorization)\n- Simple request-response patterns\n\n**Example:**\n```javascript\n// Inventory check before order\nconst inventoryResponse = await fetch('/inventory/check', {\n  method: 'POST',\n  body: JSON.stringify({ productId, quantity })\n});\n```\n\n## Asynchronous Communication (Message Queues)\n\n**Use for:**\n- Event-driven workflows (order processing pipeline)\n- Non-critical operations (email notifications, analytics)\n- Decoupling services for resilience\n\n**Example Architecture:**\n```yaml\nOrder Service → [Order Created Event] → Queue\n├── Inventory Service (reserve items)\n├── Payment Service (process payment)\n├── Notification Service (send confirmation)\n└── Analytics Service (track metrics)\n```\n\n## Recommended Pattern for E-commerce\n\n1. **Synchronous**: User-facing operations (browse, search, validate)\n2. **Asynchronous**: Background processing (order fulfillment, notifications)\n3. **Saga Pattern**: For distributed transactions across services\n\n## Implementation Tools\n\n- **Message Queues**: Apache Kafka, RabbitMQ, AWS SQS\n- **API Gateway**: Kong, Istio, AWS API Gateway\n- **Service Mesh**: For complex inter-service communication\n\n## Benefits of Hybrid Approach\n\n- **Performance**: Fast user interactions with sync calls\n- **Resilience**: Async processing continues even if some services are down\n- **Scalability**: Independent scaling of different communication patterns\n\nThis approach gives you the best of both worlds while maintaining system reliability and performance."
        }
    ]
    
    selected_topic = random.choice(topics)
    return selected_topic["title"], selected_topic["question"], selected_topic["answer"]

def generate_discussions(repos, num_discussions, temp_dir, token):
    """
    Creates GitHub discussions with accepted answers to unlock Galaxy Brain achievement.
    
    Args:
        repos (dict): Dictionary containing repository details.
        num_discussions (int): Number of discussions to create.
        temp_dir (str): Path to the temporary directory (not used for discussions).
        token (str): GitHub Personal Access Token for authentication.
    """
    print(f"\n🧠 Creating {num_discussions} discussions with accepted answers for Galaxy Brain achievement")
    print("✅ This creates real GitHub Discussions that count toward achievements")
    print("📋 Note: GitHub Discussions must be enabled on your repositories for this to work")
    print("   If you see 'No discussion categories available', enable Discussions in repo Settings > Features")
    
    for repo_name, repo_info in repos.items():
        print(f"\nProcessing repository: {repo_name}")
        
        success_count = 0
        for i in range(num_discussions):
            print(f"Creating discussion {i + 1}/{num_discussions}...")
            
            # Generate discussion content
            title, question_body, answer_body = generate_discussion_content()
            
            # Create the discussion
            result = create_discussion(repo_name, token, title, question_body)
            if result:
                discussion_number, discussion_id = result
                
                # Wait a moment before adding comment
                time.sleep(2)
                
                # Add an answer comment
                comment_id = add_discussion_comment(repo_name, token, discussion_id, answer_body)
                if comment_id:
                    # Wait a moment before marking as answer
                    time.sleep(2)
                    
                    # Mark the comment as accepted answer
                    if mark_discussion_answer(repo_name, token, comment_id):
                        success_count += 1
                        print(f"✅ Discussion #{discussion_number} completed with accepted answer")
                    else:
                        print(f"❌ Failed to mark answer for discussion #{discussion_number}")
                else:
                    print(f"❌ Failed to add comment to discussion #{discussion_number}")
            else:
                print(f"❌ Failed to create discussion {i + 1}")
            
            # Small delay between discussions to avoid rate limits
            time.sleep(3)
        
        print(f"✅ Completed {success_count}/{num_discussions} discussions for repository: {repo_name}")
        if success_count > 0:
            print("🧠 Galaxy Brain achievement progress updated!")

def get_coauthored_pull_request_count():
    """
    Prompts the user to input the number of coauthored pull requests to create.
    
    Returns:
        int: Number of coauthored pull requests to create.
    """
    try:
        num_prs = int(input("Enter the number of coauthored pull requests to create: "))
        if num_prs < 1:
            print("Number of coauthored pull requests must be at least 1.")
            sys.exit(1)
        return num_prs
    except ValueError:
        print("Invalid input. Please enter an integer.")
        sys.exit(1)

def get_coauthor_information():
    """
    Prompts the user to input coauthor information.
    
    Returns:
        list: List of coauthor strings in the format "Name <email>"
    """
    coauthors = []
    print("\n👥 Enter coauthor information for Pair Extraordinaire achievement:")
    print("💡 Tip: You can use fictional names and emails, or real collaborators")
    print("📋 Format: Name <email@example.com>")
    print("⚠️  Note: For the achievement to work, you need at least one coauthor per commit")
    
    while True:
        try:
            num_coauthors = int(input("\nHow many coauthors do you want to add? (1-5): "))
            if 1 <= num_coauthors <= 5:
                break
            else:
                print("Please enter a number between 1 and 5.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    for i in range(num_coauthors):
        print(f"\nCoauthor {i + 1}:")
        name = input("  Name: ").strip()
        email = input("  Email: ").strip()
        
        if name and email:
            coauthors.append(f"{name} <{email}>")
            print(f"  ✅ Added: {name} <{email}>")
        else:
            print("  ❌ Skipped: Name and email are required")
    
    if not coauthors:
        print("⚠️  No coauthors added. Using default coauthor for Pair Extraordinaire achievement.")
        coauthors.append("GitHub Collaborator <collaborator@example.com>")
    
    print(f"\n📝 Final coauthor list ({len(coauthors)} coauthors):")
    for i, coauthor in enumerate(coauthors, 1):
        print(f"  {i}. {coauthor}")
    
    return coauthors

def generate_coauthored_pull_requests(repos, num_prs, start_date, end_date, temp_dir, token, coauthors):
    """
    Creates coauthored pull requests for each repository across the specified date range.
    This approach creates commits on historical dates and pushes them individually.
    
    Args:
        repos (dict): Dictionary containing repository details.
        num_prs (int): Number of coauthored pull requests to create per repository.
        start_date (datetime.date): The start date for PR creation.
        end_date (datetime.date): The end date for PR creation.
        temp_dir (str): Path to the temporary directory.
        token (str): GitHub Personal Access Token for authentication.
        coauthors (list): List of coauthor strings in the format "Name <email>"
    """
    print(f"\n Creating {num_prs} coauthored pull requests from {start_date} to {end_date}")
    print("⚠️  Note: This will create commits on historical dates for proper GitHub activity tracking")
    
    # Load commit messages to use as PR titles and descriptions
    commit_messages = load_commit_messages()
    
    # Calculate date distribution for PRs
    total_days = (end_date - start_date).days + 1
    
    for repo_name, repo_info in repos.items():
        print(f"\nProcessing repository: {repo_name}")
        repo_path = clone_repo(repo_name, repo_info["url"], temp_dir)
        
        # Group PRs by date for better GitHub activity distribution
        date_groups = {}
        for i in range(num_prs):
            if total_days >= num_prs:
                day_offset = (i * total_days) // num_prs
            else:
                day_offset = random.randint(0, total_days - 1)
            pr_date = start_date + datetime.timedelta(days=day_offset)
            
            if pr_date not in date_groups:
                date_groups[pr_date] = []
            date_groups[pr_date].append(i + 1)
        
        # Process PRs grouped by date
        for pr_date, pr_indices in sorted(date_groups.items()):
            print(f"Creating {len(pr_indices)} PRs for {pr_date}")
            
            for pr_index in pr_indices:
                success = create_coauthored_pr(repo_name, repo_path, token, commit_messages, pr_index, pr_date, coauthors)
                if not success:
                    print(f"Failed to create PR {pr_index} for {repo_name}")
        
        print(f"Completed processing coauthored pull requests for repository: {repo_name}")

def create_coauthored_pr(repo_name, repo_path, token, commit_messages, pr_index, pr_date, coauthors):
    """
    Creates a coauthored pull request for a repository.
    
    Args:
        repo_name (str): The name of the repository.
        repo_path (str): The path to the cloned repository.
        token (str): GitHub Personal Access Token for authentication.
        commit_messages (list): List of commit messages to use.
        pr_index (int): The index of the PR being created.
        pr_date (datetime.date): The date for the PR.
        coauthors (list): List of coauthor strings in the format "Name <email>"
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Create a new branch
        branch_name = f"feature/coauthored-pr-{pr_index}-{pr_date.strftime('%Y%m%d')}-{random.randint(100, 999)}"
        create_branch(repo_path, branch_name)
        
        # Create 1-3 commits with historical dates
        num_commits = random.randint(1, 3)
        for commit_num in range(num_commits):
            # Create unique file
            timestamp = datetime.datetime.combine(pr_date, datetime.time(
                hour=random.randint(9, 17),
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )) + datetime.timedelta(hours=commit_num * 2)
            
            file_name = f"coauthored_pr_{pr_index}_{commit_num + 1}_{random.randint(1000, 9999)}.txt"
            file_path = os.path.join(repo_path, file_name)
            
            # Create file content
            with open(file_path, "w") as f:
                f.write(f"Coauthored Pull Request #{pr_index} - Commit {commit_num + 1}\n")
                f.write(f"Date: {pr_date.isoformat()}\n")
                f.write(f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Feature: {random.choice(commit_messages)}\n")
                f.write(f"Branch: {branch_name}\n")
            
            # Stage and commit with historical date and coauthors
            run_command(["git", "add", file_name], cwd=repo_path)
            
            # Create commit message with coauthors for Pair Extraordinaire achievement
            base_message = f"Add feature {pr_index}.{commit_num + 1}: {random.choice(commit_messages)}"
            
            # Add coauthor information to commit message
            coauthor_lines = []
            for coauthor in coauthors:
                coauthor_lines.append(f"Co-authored-by: {coauthor}")
            
            # Combine base message with coauthor information
            if coauthor_lines:
                commit_message = base_message + "\n\n" + "\n".join(coauthor_lines)
            else:
                commit_message = base_message
            
            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = timestamp.strftime("%Y-%m-%dT%H:%M:%S")
            env["GIT_COMMITTER_DATE"] = timestamp.strftime("%Y-%m-%dT%H:%M:%S")
            
            run_command(["git", "commit", "-m", commit_message], cwd=repo_path, env=env)
        
        # Push the branch
        run_command(["git", "push", "-u", "origin", branch_name], cwd=repo_path)
        
        # Create the pull request with coauthor information
        pr_title = f"🤝 Coauthored Feature {pr_index}: {random.choice(commit_messages)}"
        pr_body = f"This coauthored pull request implements feature {pr_index} for Pair Extraordinaire achievement.\n\n"
        pr_body += f"📅 Developed on: {pr_date.strftime('%Y-%m-%d')}\n"
        pr_body += f"👥 Coauthors ({len(coauthors)}):\n"
        for coauthor in coauthors:
            pr_body += f"- {coauthor}\n"
        pr_body += f"\n🚀 Features:\n"
        for i in range(num_commits):
            pr_body += f"- {random.choice(commit_messages)}\n"
        pr_body += f"\n✨ This PR contains {num_commits} coauthored commit(s) that will count toward the Pair Extraordinaire achievement."
        
        pr_number = create_pull_request(repo_name, token, branch_name, pr_title, pr_body)
        
        if pr_number:
            # Merge the PR immediately
            merge_success = merge_pull_request(repo_name, token, pr_number)
            if merge_success:
                # Switch back to main branch
                run_command(["git", "checkout", "main"], cwd=repo_path)
                return True
        
        return False
        
    except Exception as e:
        print(f"Error creating coauthored PR {pr_index}: {e}")
        # Try to switch back to main branch even if there was an error
        try:
            run_command(["git", "checkout", "main"], cwd=repo_path)
        except:
            pass
        return False

def get_coauthored_pull_request_date_range():
    """
    Prompts the user to input the start and end dates for coauthored pull request creation.
    
    Returns:
        tuple: Start date and end date as datetime.date objects.
    """
    print("\nChoose date range for coauthored pull requests:")
    print("1. Last 30 days")
    print("2. Last 3 months")
    print("3. Last 6 months")
    print("4. Last year")
    print("5. Custom date range")
    
    choice = input("Enter your choice (1-5): ").strip()
    
    today = datetime.date.today()
    
    if choice == '1':
        start_date = today - datetime.timedelta(days=30)
        end_date = today
        print(f"Selected: Last 30 days ({start_date} to {end_date})")
    elif choice == '2':
        start_date = today - datetime.timedelta(days=90)
        end_date = today
        print(f"Selected: Last 3 months ({start_date} to {end_date})")
    elif choice == '3':
        start_date = today - datetime.timedelta(days=180)
        end_date = today
        print(f"Selected: Last 6 months ({start_date} to {end_date})")
    elif choice == '4':
        start_date = today - datetime.timedelta(days=365)
        end_date = today
        print(f"Selected: Last year ({start_date} to {end_date})")
    elif choice == '5':
        try:
            start_date_str = input("Enter start date for PRs (YYYY-MM-DD): ").strip()
            end_date_str = input("Enter end date for PRs (YYYY-MM-DD): ").strip()
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
            if start_date > end_date:
                print("Start date must be before end date.")
                sys.exit(1)
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            sys.exit(1)
    else:
        print("Invalid choice. Please enter a number between 1 and 5.")
        sys.exit(1)
    
    return start_date, end_date

if __name__ == "__main__":
    main()
