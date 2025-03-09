import requests
import os

# Replace with your GitHub repo details
GITHUB_REPO = "nvminh/ai-code-review-bot"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def fetch_pr_diff(pr_number):
    """Fetches the PR diff from GitHub."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Error fetching PR files: {response.json()}")
        return ""

    return "\n".join([f["patch"] for f in response.json() if "patch" in f])

def ai_review(diff):
    """Calls the AI model to review the PR diff."""
    if not diff:
        return "No code changes detected."
    
    # Using a local AI model like Ollama (or replace with another LLM API)
    return os.popen(f"ollama run codellama 'Review this code:\n{diff}'").read()

def post_comment(pr_number, feedback):
    """Posts the AI review feedback as a comment on the PR."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": f"🤖 AI Review:\n\n{feedback}"}
    print(f"🔍 Posting data: {data}")

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print("✅ AI review comment posted successfully!")
    else:
        print(f"❌ Failed to post comment: {response.json()}")

if __name__ == "__main__":
    pr_number = os.getenv("PR_NUMBER")
    if not pr_number:
        print("❌ PR number is required. Exiting...")
        exit(1)

    print(f"🔍 Fetching PR #{pr_number} diff...")
    diff = fetch_pr_diff(pr_number)

    print("🤖 Running AI code review...")
    feedback = ai_review(diff)

    print("💬 Posting AI review comment on PR...")
    post_comment(pr_number, feedback)

