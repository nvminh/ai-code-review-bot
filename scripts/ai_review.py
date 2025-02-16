import requests
import os

def fetch_pr_diff(pr_url):
    response = requests.get(pr_url, headers={"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"})
    return "\n".join([f["patch"] for f in response.json()])

def ai_review(diff):
    return os.popen(f"ollama run codellama 'Review this code:\n{diff}'").read()

if __name__ == "__main__":
    pr_url = "https://api.github.com/repos/YOUR_REPO_OWNER/YOUR_REPO_NAME/pulls/1/files"
    diff = fetch_pr_diff(pr_url)
    feedback = ai_review(diff)
    print(feedback)

