import requests
import os
import json

# GitHub repo details
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o"

def fetch_pr_details(pr_number):  # ✨ NEW
    """Fetches PR title and description."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Error fetching PR details: {response.json()}")
        return {}
    return response.json()

def fetch_pr_comments(pr_number):  # ✨ NEW
    """Fetches PR-level comments."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Error fetching PR comments: {response.json()}")
        return []
    return [c["body"] for c in response.json()]

def fetch_pr_files(pr_number):
    """Fetches PR files with diffs from GitHub."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Error fetching PR files: {response.json()}")
        return []

    return response.json()

def fetch_latest_commit(pr_number):
    """Fetches the latest commit SHA for the PR."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}/commits"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        commits = response.json()
        return commits[-1]["sha"]
    else:
        print(f"❌ Failed to fetch latest commit: {response.json()}")
        return None

def get_diff_positions(pr_number):
    """Fetches GitHub diff positions for PR files."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Error fetching PR diff positions: {response.json()}")
        return {}

    files = response.json()
    positions = {}

    for file in files:
        filename = file["filename"]
        if "patch" in file:
            lines = file["patch"].split("\n")
            line_number = None
            position = 1

            for line in lines:
                if line.startswith("@@"):
                    parts = line.split(" ")
                    new_part = parts[2]
                    start_line = int(new_part.split(",")[0][1:])
                    line_number = start_line
                elif line.startswith("+"):
                    positions.setdefault(filename, {})[line_number] = position
                    position += 1
                line_number += 1

    return positions

def ai_review(files, pr_details, pr_comments):  # ✨ UPDATED
    """Calls OpenAI API to review the PR and return structured JSON feedback with suggestions if not approved."""
    if not files:
        return {"feedback": "No code changes detected.", "approve": False, "comments": [], "suggestions": []}

    diffs = "\n".join([f"{f['filename']}:\n{f['patch']}" for f in files if "patch" in f])
    pr_title = pr_details.get("title", "")
    pr_body = pr_details.get("body", "")
    comments_text = "\n".join(pr_comments)

    prompt = f"""
    You are an AI code reviewer. The following is a Pull Request:

    Title:
    {pr_title}

    Description:
    {pr_body}

    Reviewer comments so far:
    {comments_text}

    Code changes:
    {diffs}

    Please analyze and return:
    {{
        "feedback": "General feedback on the PR",
        "approve": true/false,
        "comments": [
            {{"file_path": "src/main/MyClass.java", "line_number": 12, "comment": "Consider using a more efficient algorithm."}}
        ],
        "suggestions": ["Refactor function X to improve readability.", "Add unit tests for feature Y."]
    }}
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
            return {"feedback": "AI review failed to parse response.", "approve": False, "comments": [], "suggestions": []}
    else:
        print(f"❌ OpenAI API error: {response.json()}")
        return {"feedback": "AI review failed due to API error.", "approve": False, "comments": [], "suggestions": []}

def post_general_comment(pr_number, feedback, approve, suggestions):
    """Posts the AI review summary and suggestions as a general comment on the PR."""
    if not approve:
        feedback += "\n\n🚨 AI did not approve this PR. Please review the comments and make necessary changes."
        if suggestions:
            feedback += "\n\n💡 **How to get this PR approved:**\n"
            feedback += "\n".join([f"- {s}" for s in suggestions])

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
        print(f"❌ Failed to post general comment: {response.json()}")

def post_inline_comment(pr_number, commit_id, file_path, line_number, comment, diff_positions):
    """Posts an inline comment on a specific modified line in the PR."""
    if file_path not in diff_positions or line_number not in diff_positions[file_path]:
        print(f"⚠️ Skipping inline comment: No diff position found for {file_path}:{line_number}")
        return

    position = diff_positions[file_path][line_number]

    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "body": comment,
        "commit_id": commit_id,
        "path": file_path,
        "position": position,  # ✅ Now using the correct GitHub diff position
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"✅ Inline comment posted on {file_path}:{line_number} (GitHub diff position: {position})")
    else:
        print(f"❌ Failed to post inline comment: {response.json()}")

def approve_pr(pr_number):
    """Approves the PR using GitHub API."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}/reviews"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
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

    print(f"🔍 Fetching PR #{pr_number} details...")
    pr_details = fetch_pr_details(pr_number)
    pr_comments = fetch_pr_comments(pr_number)

    print("🔍 Fetching PR files...")
    files = fetch_pr_files(pr_number)

    print("🧐 Mapping diff positions...")
    diff_positions = get_diff_positions(pr_number)

    print("🤖 Running AI code review...")
    review = ai_review(files, pr_details, pr_comments)

    print("💬 Posting AI review summary on PR...")
    post_general_comment(pr_number, review["feedback"], review["approve"], review.get("suggestions", []))

    commit_id = fetch_latest_commit(pr_number)
    if not commit_id:
        print("⚠️ Skipping inline comments due to missing commit ID.")
    else:
        print("💬 Posting inline comments...")
        for comment in review["comments"]:
            post_inline_comment(pr_number, commit_id, comment["file_path"], comment["line_number"], comment["comment"], diff_positions)

    if review["approve"]:
        print("✅ AI approves this PR. Sending approval...")
        approve_pr(pr_number)
    else:
        print("⚠️ AI did not approve the PR.")
