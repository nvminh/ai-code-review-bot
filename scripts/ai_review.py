import requests
import os

# Replace with your actual repo name
GITHUB_REPO = "nvminh/ai-code-review-bot"

def fetch_pr_diff(pr_number):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching PR files: {response.json()}")
        return ""

    return "\n".join([f["patch"] for f in response.json() if "patch" in f])

def ai_review(diff):
    if not diff:
        return "No code changes found for review."
    
    # Using a local LLM like Ollama (install with `brew install ollama`)
    return os.popen(f"ollama run codellama 'Review this code:\n{diff}'").read()

if __name__ == "__main__":
    pr_number = 1  # Change to the actual PR number when testing
    diff = fetch_pr_diff(pr_number)
    feedback = ai_review(diff)
    
    print("\n🔍 AI Code Review Feedback:\n")
    print(feedback)


