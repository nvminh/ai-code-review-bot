import requests
import os

GITHUB_REPO = "nvminh/ai-code-review-bot"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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
    """Calls OpenAI GPT API to review the PR diff."""
    if not diff:
        return "No code changes detected."

    openai_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "gpt-4",
        "messages": [{"role": "system", "content": "You are a code reviewer."},
                     {"role": "user", "content": f"Review this code:\n{diff}"}],
        "max_tokens": 500
    }

    response = requests.post(openai_url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"❌ OpenAI API error: {response.json()}")
        return "AI review failed."

    return response.json()["choices"][0]["message"]["content"]

def post_comment(pr_number, feedback):
    """Posts the AI review feedback as a comment on the PR."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": f"🤖 AI Review:\n\n{feedback}"}

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


