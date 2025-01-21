# GitCommitAssistant 🚀


## Description 📝

**GitCommitAssistant** is an open-source tool designed to help developers manage their GitHub repositories by automating commit messages. Whether you're looking to maintain a consistent commit history for personal projects, manage multiple repositories efficiently, or ensure regular updates, GitCommitAssistant provides a streamlined solution.

> **⚠️ Disclaimer:** This tool is intended for legitimate use cases such as managing multiple repositories, maintaining project consistency, or educational purposes. Misuse of this tool to fabricate commit histories or deceive others is strongly discouraged and violates GitHub's [Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service).

## Table of Contents 📚

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Getting Started with Personal Access Tokens](#getting-started-with-personal-access-tokens)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features 🌟

- **Automated Commit Generation:** Create meaningful and consistent commit messages across multiple repositories.
- **Customizable Commit Frequency:** Choose how often commits are made, ranging from daily to random intervals.
- **Personalized Commit Messages:** Use default professional messages or provide your own for each repository.
- **Repository Management:** Automatically create new repositories if you don't have any.
- **User-Friendly Interface:** Interactive prompts guide you through the setup and usage process.
- **Loading Indicators:** Visual feedback during processing to enhance user experience.

## Installation 🛠️

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/GitCommitAssistant.git
   ```

2. **Navigate to the Project Directory:**

   ```bash
   cd GitCommitAssistant
   ```

3. **Install Required Dependencies:**

   Ensure you have Python 3.6 or higher installed. Then, install the necessary Python packages:

   ```bash
   pip install -r requirements.txt
   ```

## Usage 💻

1. **Run the Script:**

   ```bash
   python GitCommitAssistant.py
   ```

2. **Follow the Prompts:**

   - **Repository Setup:**
     - Indicate whether you have existing repositories.
     - If not, the tool will assist in creating new ones.
   - **Date Range:**
     - Specify the start and end dates for commit generation.
   - **Commit Frequency:**
     - Define the minimum and maximum number of commits per day.
   - **Commit Messages:**
     - Choose to use default messages or provide custom ones for each repository.

3. **Monitor the Process:**

   A green spinning indicator will display while the tool processes commits. Once completed, you'll receive a confirmation message.

## Getting Started with Personal Access Tokens 🔑

To allow GitCommitAssistant to interact with your GitHub account, you need to generate a Personal Access Token (PAT). Follow these steps:

1. **Sign In to GitHub:**
   - Visit [GitHub](https://github.com/) and log in to your account.

2. **Navigate to Settings:**
   - Click on your profile picture in the top-right corner.
   - Select **"Settings"** from the dropdown menu.

3. **Access Developer Settings:**
   - In the left sidebar, click on **"Developer settings"**.

4. **Go to Personal Access Tokens:**
   - Click on **"Personal access tokens"**.
   - Select **"Tokens (classic)"** if prompted.

5. **Generate a New Token:**
   - Click the **"Generate new token"** button.
   - Enter your GitHub password if prompted.

6. **Configure Token Settings:**
   - **Note:** GitHub recommends using fine-grained tokens for enhanced security.
   - **For Classic Tokens:**
     - **Note:** Classic tokens are being phased out in favor of fine-grained tokens.

7. **Set a Note:**
   - Provide a descriptive name (e.g., "GitCommitAssistant Automation").

8. **Set Expiration:**
   - Choose an expiration date for security purposes.

9. **Select Scopes:**
   - **`repo`**: Full control of private repositories.
   - **`admin:repo_hook`**: Manage repository hooks.
   - **`user`**: Read and write access to profile information.

10. **Generate the Token:**
    - Click **"Generate token"** at the bottom.

11. **Copy the Token:**
    - **Important:** Copy and store your token securely. You won't be able to view it again.

12. **Use the Token in GitCommitAssistant:**
    - When prompted by the tool, paste your PAT.

> **🔒 Security Tip:** Store your PAT securely and avoid sharing it. If compromised, revoke it immediately from your GitHub settings.

## FAQ ❓

**Q1: Is it ethical to use GitCommitAssistant to fake commits?**

**A1:** No. GitCommitAssistant is intended for legitimate purposes such as managing multiple repositories, maintaining project consistency, or educational use. Fabricating commit histories to deceive others violates ethical guidelines and GitHub's [Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service).

**Q2: Can I customize commit messages for each repository?**

**A2:** Yes. You can edit the commit_messages.txt file and add the custom messages that you need!

**Q3: What permissions does GitCommitAssistant require?**

**A3:** The tool requires a Personal Access Token with specific scopes, primarily `repo`, `admin:repo_hook`, and `user`, to manage repositories and commit changes.

**Q4: How can I contribute to GitCommitAssistant?**

**A4:** See the [Contributing](#contributing) section below for guidelines.

**Q5: What should I do if I encounter an error during usage?**

**A5:** Ensure you have the correct permissions set for your Personal Access Token and that your repositories are accessible. If issues persist, feel free to open an issue on the repository.

## Contributing 🤝

Contributions are welcome! To ensure a smooth process, please follow these guidelines:

1. **Fork the Repository:**

   Click the **"Fork"** button at the top-right corner of the repository page.

2. **Clone Your Fork:**

   ```bash
   git clone https://github.com/yourusername/GitCommitAssistant.git
   ```

3. **Create a New Branch:**

   ```bash
   git checkout -b feature/YourFeatureName
   ```

4. **Make Your Changes:**

   Implement your feature or bug fix.

5. **Commit Your Changes:**

   ```bash
   git commit -m "Add Your Feature Description"
   ```

6. **Push to Your Fork:**

   ```bash
   git push origin feature/YourFeatureName
   ```

7. **Create a Pull Request:**

   Navigate to the original repository and click **"Compare & pull request"**.

8. **Describe Your Changes:**

   Provide a clear description of what you've done and why.

9. **Wait for Review:**

   Maintainers will review your pull request and provide feedback or merge it.

### Code of Conduct 🛡️

Please adhere to the [Code of Conduct](CODE_OF_CONDUCT.md) when contributing to this project.

## License 📄

This project is licensed under the [MIT License](LICENSE).

> **MIT License**
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.

## Contact 📫

For any questions or support, please open an issue on the [GitHub repository](https://github.com/yourusername/GitCommitAssistant) or contact [samsiavoshian2009@gmail.com](mailto:samsiavoshian2009@gmail.com).

---
**GitCommitAssistant** is maintained by Saam Siavoshian ([GitHub](https://github.com/sam-siavoshian)). Thank you for using this tool responsibly! 😊
