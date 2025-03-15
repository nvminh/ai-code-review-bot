import requests
import os
import json

# GitHub repo details
GITHUB_REPO = "nvminh/ai-code-review-bot"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_PAT = os.getenv("GH_PAT")
OPENAI_MODEL = "gpt-4o"  # Change to a model you have access to

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
    """Calls OpenAI API to review the PR and return structured JSON."""
    if not diff:
        return {"feedback": "No code changes detected.", "approve": False}

    prompt = f"""
    You are an AI code reviewer. Review the following code changes and return a JSON response.
    The response should include:
    - "feedback": A summary of the review
    - "approve": true if the code is good, false if issues are found
    
    Code changes:
    {diff}
    
    Respond in JSON format like this:
    {{"feedback": "Your review text here", "approve": true}}
    """

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            json_response = response.json()
            return json.loads(json_response["choices"][0]["message"]["content"])
        except (KeyError, json.JSONDecodeError):
            print(f"⚠️ Unexpected AI response: {json_response}")
            return {"feedback": "AI review failed to parse response.", "approve": False}
    else:
        print(f"❌ OpenAI API error: {response.json()}")
        return {"feedback": "AI review failed due to API error.", "approve": False}

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

def approve_pr(pr_number):
    """Approves the PR using GitHub API."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}/reviews"
    headers = {
        "Authorization": f"token {GITHUB_PAT}",  # ✅ Use GH_PAT instead of GITHUB_TOKEN
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"event": "APPROVE"}

    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print("✅ PR approved successfully!")
    else:
        print(f"❌ Failed to approve PR: {response.json()}")

if __name__ == "__main__":
    pr_number = os.getenv("PR_NUMBER")
    if not pr_number:
        print("❌ PR number is required. Exiting...")
        exit(1)

    print(f"🔍 Fetching PR #{pr_number} diff...")
    diff = fetch_pr_diff(pr_number)

    print("🤖 Running AI code review...")
    review = ai_review(diff)

    print("💬 Posting AI review comment on PR...")
    post_comment(pr_number, review["feedback"])

    if review["approve"]:
        print("✅ AI approves this PR. Sending approval...")
        approve_pr(pr_number)
    else:
        print("⚠️ AI did not approve the PR.")



