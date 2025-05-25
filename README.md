
# 🤖 AI Code Review Bot

This repository provides an AI-powered code review bot that automatically reviews pull requests using OpenAI's GPT models. It provides general feedback and inline comments on code changes and can also approve PRs if no issues are found.

---
## ✨ Features

✅ Fetches PR diffs and reviews them using OpenAI  
✅ Provides general feedback on the PR  
✅ Posts inline comments on specific lines of code  
✅ Suggests improvements when the PR is not approved  
✅ Approves PRs if no issues are found

## 🚀 Getting Started

### 1️⃣ Fork & Clone the Repository

To use the bot in your project, fork this repository and clone it to your local machine:

```sh
git clone git@github.com:nvminh/ai-code-review-bot.git
cd ai-code-review-bot
```

### 2️⃣ Set Up GitHub Actions
The bot is designed to run automatically as a GitHub Action whenever a pull request is created or updated.

To enable it, simply copy the `.github/workflows/ai-review.yml` file from this repository to your project’s `.github/workflows/` directory.

If you don’t have a `.github/workflows/` folder in your project, create one and then add the workflow file.

### 3️⃣ Add API Key for OpenAI
Since the bot uses OpenAI for reviewing code, you need to set up the **OpenAI API Key** in your repository’s **GitHub Secrets**.

1. Go to **Settings → Secrets and variables → Actions** in your GitHub repository.
2. Click **New repository secret**.
3. Name it **OPENAI_API_KEY** and paste your OpenAI API key as the value.

### 4️⃣ Trigger AI Code Review
Once the workflow is set up, the AI Code Review Bot will run automatically whenever a pull request is created or updated. The bot will:

1. Fetch PR changes and analyze them using OpenAI.
2. Post general feedback as a comment on the PR.
3. Add inline comments for specific suggestions.
4. If no major issues are found, the bot will approve the PR.
5. If issues are detected, the bot will **not approve** the PR and will provide **clear suggestions on how to get it approved**.

---
## 🛠 How It Works
### 1️⃣ Fetching PR Files

* The bot retrieves all modified files in the pull request and their corresponding diffs.
### 2️⃣ AI Review Process

* The AI analyzes the code changes and returns a structured JSON response with feedback, inline comments, and suggestions.
### 3️⃣ Posting Comments

* The bot posts a general review summary as a comment on the PR.
* If necessary, the bot also posts inline comments on specific lines of code.
### 4️⃣ Approval Decision

* ✅ If no critical issues are found, the bot automatically approves the PR.
* ❌ If issues are found, the bot does not approve the PR and provides suggestions on what needs to be improved.

---
## ❓ FAQ
### 1️⃣ What happens if the AI does not approve a PR?
If the bot does not approve the PR, it will leave a **detailed review comment** explaining why. It will also include **specific suggestions** on how to fix the issues and get the PR approved.

### 2️⃣ Do I need to set up a GitHub token?
No, the bot uses the built-in **GITHUB_TOKEN**, so no additional setup is required.

### 3️⃣ Can I modify the AI review criteria?
Yes! You can modify `scripts/ai_review.py` to adjust the prompt for OpenAI or change how approvals are handled.

### 4️⃣ How do I disable automatic PR approval?
To disable auto-approval, modify the workflow file and remove the `approve_pr(pr_number)` function call in `scripts/ai_review.py`.

---
## 💡 Contributing
We welcome contributions! Feel free to submit pull requests to improve the bot or enhance its AI review capabilities.
