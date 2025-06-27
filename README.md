# GitCommitAssistant 🚀

**GitCommitAssistant** is a powerful Python tool designed to help developers automate their GitHub repository activity and unlock GitHub achievements. Whether you want to fill your contribution graph, increase your pull request count, earn discussion achievements, or unlock the coveted "Pair Extraordinaire" achievement, this tool has you covered!

## Features 🌟

- **Automated Commit Generation:** Create meaningful and consistent commit messages across multiple repositories.
- **Historical Commit Generation:** Generate commits that simulate pull request activity with proper backdating for GitHub activity charts.
- **GitHub Discussions with Accepted Answers:** Create discussions with accepted answers to unlock the "Galaxy Brain" achievement.
- **Coauthored Pull Requests:** Create pull requests with properly formatted coauthored commits to unlock the "Pair Extraordinaire" achievement.
- **Achievement Troubleshooting:** Built-in fixes for common GitHub achievement issues.
- **Customizable Commit Frequency:** Choose how often commits are made, ranging from daily to random intervals.
- **Personalized Commit Messages:** Use default professional messages or provide your own for each repository.
- **Repository Management:** Automatically create new repositories if you don't have any.
- **User-Friendly Interface:** Interactive prompts guide you through the setup and usage process.
- **Lightweight and Fast:** Minimal dependencies and efficient processing with parallel operations.

## Recent Updates 🆕

### v2.1 - Achievement Fix Update
- **🔧 Fixed Coauthor Format:** Coauthored commits now include proper `Co-authored-by:` lines that GitHub recognizes
- **🧠 Enhanced Galaxy Brain:** Improved discussion creation with Q&A category detection
- **📊 Achievement Troubleshooting:** Added comprehensive troubleshooting guide for missing achievements
- **⚡ Performance Improvements:** Optimized parallel processing for faster execution

## GitHub Achievements Supported 🏆

| Achievement | Description | Status |
|-------------|-------------|---------|
| **Pull Shark** | Merged pull requests | ✅ Supported |
| **Galaxy Brain** | Accepted discussion answers | ✅ Supported |  
| **Pair Extraordinaire** | Coauthored commits on merged PRs | ✅ Fixed & Supported |
| **YOLO** | Merged PR without review | ✅ Automatic |
| **Quickdraw** | Quick issue/PR closure | ✅ Manual |

## Installation 📦

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sam-siavoshian/GitCommitAssistant.git
   cd GitCommitAssistant
   ```

2. **Install dependencies:**
   ```bash
   pip install requests
   ```

3. **Set up your GitHub Personal Access Token:**
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate a new token with `repo`, `workflow`, and `discussions:write` scopes
   - Keep this token secure!

## Usage 🎯

1. **Run the script:**
   ```bash
   python3 GitCommitAssistant.py
   ```

2. **Choose Your Operation:**
   - Select whether you want to generate commits, create pull requests, create discussions with accepted answers, or create coauthored pull requests.

3. **Repository Setup:**
   - Choose to use existing repositories or create new ones.
   - Provide repository names and GitHub URLs.

4. **For Commit Generation:**
   - **Commit Frequency:**
     - Choose how often you want commits to be made (daily, every few days, weekly, or random).
   - **Date Range:**
     - Specify the start and end dates for commit generation.
   - **Commit Messages:**
     - Use default messages or provide custom ones for each repository.

5. **For Pull Request Creation:**
   - **Repository Setup:**
     - Similar to commit generation, set up your repositories.
   - **Pull Request Count:**
     - Specify how many pull requests to create for each repository.
   - **Date Range:**
     - Specify the start and end dates for pull request creation (allows backdating).
   - **Authentication:**
     - Provide your GitHub Personal Access Token for API access.

6. **For Discussion Creation:**
   - **Repository Setup:**
     - Set up your repositories (same as other options).
   - **Discussion Count:**
     - Specify how many discussions to create for each repository.
   - **Authentication:**
     - Provide your GitHub Personal Access Token for API access.
   - **Prerequisites:**
     - GitHub Discussions must be enabled on your repositories.
     - Go to repository Settings → Features → Check "Discussions"
     - Ensure Q&A category is available (supports marking answers)

7. **For Coauthored Pull Request Creation:**
   - **Repository Setup:**
     - Set up your repositories (same as other options).
   - **Pull Request Count:**
     - Specify how many coauthored pull requests to create for each repository.
   - **Date Range:**
     - Choose the date range for pull request creation (supports historical dates).
   - **Coauthor Information:**
     - Add 1-5 coauthors with names and email addresses.
     - Can use fictional collaborators for achievement purposes.
   - **Authentication:**
     - Provide your GitHub Personal Access Token for API access.

## Achievement Troubleshooting 🔧

### If Your Achievements Aren't Showing Up:

1. **Check Profile Settings (Most Common Issue):**
   - Go to: https://github.com/settings/profile
   - Scroll to "Achievements" section
   - Ensure "Show Achievements on my profile" is **CHECKED** ✅

2. **Wait for Processing:**
   - GitHub achievements can take **24-48 hours** to appear
   - Be patient after meeting requirements

3. **Verify Requirements:**
   - **Galaxy Brain:** Need 2+ accepted discussion answers
   - **Pair Extraordinaire:** Need 1+ coauthored commit on merged PR
   - **Pull Shark:** Need 2+ merged pull requests

4. **Check Repository Visibility:**
   - Achievements typically only count for **public repositories**
   - Ensure your repositories are public

5. **Verify Coauthor Format:**
   - Commit messages must include: `Co-authored-by: Name <email@example.com>`
   - This tool now automatically formats this correctly

## Example Output 📸

```
Welcome to GitCommitAssistant!
What would you like to do?
1. Generate commits
2. Create actual pull requests (will increase PR count in activity chart)
3. Create discussions with accepted answers (for Galaxy Brain achievement)
4. Create coauthored pull requests (for Pair Extraordinaire achievement)

🤝 Creating coauthored pull requests for Pair Extraordinaire achievement
✅ This creates real GitHub PRs with properly formatted coauthored commits
👥 Added coauthors: John Doe <john@example.com>, Jane Smith <jane@example.com>
📝 Pull request #5 created successfully with 3 coauthored commits
🎉 Pull request #5 merged successfully - achievement progress updated!
```

## Requirements 📋

- **Python 3.6+**
- **Git** (installed and configured)
- **GitHub Personal Access Token** (for API operations)
- **Internet connection**
- **Public GitHub repositories** (for achievements to count)

## Security 🔒

- Your GitHub Personal Access Token is used only for API calls and is not stored.
- All operations are performed on your own repositories.
- The tool follows GitHub's API rate limits and best practices.
- Coauthor emails can be fictional for achievement purposes.

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer ⚠️

This tool is designed to help developers showcase their work and earn legitimate GitHub achievements. Please use it responsibly and in accordance with GitHub's Terms of Service. The achievements earned reflect the automated activity generated by this tool.

## Support 💬

If you encounter any issues or have questions:
1. Check the troubleshooting section above
2. Ensure your GitHub Personal Access Token has the correct permissions
3. Verify that your repositories have the necessary features enabled (Discussions, etc.)
4. Wait 24-48 hours for achievements to appear after meeting requirements

---

**Happy Coding!** 🎉

*Made with ❤️ for the GitHub community*
