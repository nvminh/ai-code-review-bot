import requests
import os
import json

# GitHub repo details
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# OPENAI_MODEL = "gpt-4.1"
# OPENAI_MODEL = "gpt-4.1-mini"
OPENAI_MODEL = "gpt-4.1-nano"

AI_COMMENT_TAG = "🤖 AI Review:"

MODEL_PRICING = {
    "gpt-4.1": {
        "input_per_million": 2.00,
        "output_per_million": 8.00
    },
    "gpt-4.1-mini": {
        "input_per_million": 0.40,
        "output_per_million": 1.60
    },
    "gpt-4.1-nano": {
        "input_per_million": 0.10,
        "output_per_million": 0.40
    }
}

def estimate_cost(model_name, prompt_tokens, completion_tokens):
    pricing = MODEL_PRICING.get(model_name)
    if not pricing:
        print(f"⚠️ Unknown model: {model_name}. Cannot estimate cost.")
        return 0.0

    cost_prompt = (prompt_tokens / 1_000_000) * pricing["input_per_million"]
    cost_completion = (completion_tokens / 1_000_000) * pricing["output_per_million"]
    return cost_prompt + cost_completion

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

def ai_review(files, pr_description):
    """Calls OpenAI API to review the PR."""
    if not files:
        return {"feedback": "No code changes detected.", "approve": False, "comments": [], "suggestions": []}

    diffs = "\n".join([f"{f['filename']}:\n{f['patch']}" for f in files if "patch" in f])

    prompt = f"""
    You are an AI code reviewer. Analyze the PR description and code changes below. Return a JSON with:
    - "feedback": summary of the review
    - "approve": true/false
    - "comments": inline comments
    - "suggestions": steps needed for approval

    PR description:
    {pr_description}

    Code changes:
    {diffs}

    Return JSON:
    {{
        "feedback": "General feedback on the PR",
        "approve": true/false,
        "comments": [
            {{"file_path": "src/main/MyClass.java", "line_number": 12, "comment": "Consider using a more efficient algorithm."}}
        ],
        "suggestions": [
            "Refactor function X to improve readability.", "Add unit tests for feature Y."
        ]
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
            usage = json_response.get("usage", {"prompt_tokens": 0, "completion_tokens": 0})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)

            cost = estimate_cost(OPENAI_MODEL, prompt_tokens, completion_tokens)

            print(f"💡 OpenAI API usage: prompt {prompt_tokens}, completion {completion_tokens}, cost ≈ ${cost:.6f} USD")

            # Attach to result so it can be posted
            review = json.loads(json_response["choices"][0]["message"]["content"])
            review["usage"] = usage
            review["cost"] = cost
            return review
        except (KeyError, json.JSONDecodeError):
            print(f"⚠️ Unexpected AI response: {json_response}")
            return {"feedback": "AI review failed to parse response.", "approve": False, "comments": [], "suggestions": [], "usage": {"prompt_tokens": 0, "completion_tokens": 0}, "cost": 0}
    else:
        print(f"❌ OpenAI API error: {response.json()}")
        return {"feedback": "AI review failed due to API error.", "approve": False, "comments": [], "suggestions": [], "usage": {"prompt_tokens": 0, "completion_tokens": 0}, "cost": 0}

def fetch_existing_comments(pr_number):
    """Fetches all PR review comments."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed to fetch existing comments: {response.json()}")
        return []

def delete_comment(comment_id):
    """Deletes a comment by ID."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/comments/{comment_id}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print(f"✅ Deleted old AI comment ID: {comment_id}")
    else:
        print(f"❌ Failed to delete comment ID {comment_id}: {response.json()}")

def fetch_inline_comments(pr_number):
    """Fetches all review comments (inline) for the PR."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}/comments"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed to fetch inline review comments: {response.json()}")
        return []

def delete_inline_comment(comment_id):
    """Deletes an inline review comment by ID."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/comments/{comment_id}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print(f"✅ Deleted old AI inline comment ID: {comment_id}")
    else:
        print(f"❌ Failed to delete inline comment ID {comment_id}: {response.json()}")

def cleanup_old_ai_comments(pr_number):
    """Deletes old AI comments (both issue-level and inline)."""
    # Issue-level comments
    issue_comments = fetch_existing_comments(pr_number)
    for comment in issue_comments:
        if comment["body"].startswith(AI_COMMENT_TAG):
            delete_comment(comment["id"])

    # Inline review comments
    inline_comments = fetch_inline_comments(pr_number)
    for comment in inline_comments:
        if comment["body"].startswith(AI_COMMENT_TAG):
            delete_inline_comment(comment["id"])

def post_general_comment(pr_number, feedback, approve, suggestions, usage, cost):
    """Posts the AI review summary and suggestions as a general comment."""
    if not approve:
        feedback += "\n\n🚨 AI did not approve this PR. Please review the comments and make necessary changes."
        if suggestions:
            feedback += "\n\n💡 **How to get this PR approved:**\n"
            feedback += "\n".join([f"- {s}" for s in suggestions])

    feedback += f"\n\n📊 **AI review usage:** Prompt tokens: {usage.get('prompt_tokens', 0)}, Completion tokens: {usage.get('completion_tokens', 0)}, Estimated cost: ${cost:.6f} USD (model: {OPENAI_MODEL})"

    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": f"{AI_COMMENT_TAG}\n\n{feedback}"}

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
        "body": f"{AI_COMMENT_TAG} {comment}",
        "commit_id": commit_id,
        "path": file_path,
        "position": position
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"✅ Inline comment posted on {file_path}:{line_number}")
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

    print(f"🔍 Fetching PR #{pr_number} files...")
    files = fetch_pr_files(pr_number)

    print("🧹 Cleaning up old AI comments...")
    cleanup_old_ai_comments(pr_number)

    print("🧐 Mapping diff positions...")
    diff_positions = get_diff_positions(pr_number)

    print("📄 Fetching PR description...")
    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    pr_description = response.json().get("body", "")

    print("🤖 Running AI code review...")
    review = ai_review(files, pr_description)

    print("💬 Posting AI review summary on PR...")
    post_general_comment(pr_number, review["feedback"], review["approve"], review.get("suggestions", []), review["usage"], review["cost"])

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
