import os
import sys
import json
import base64
import requests

# Load variables from environment
GITLAB_TOKEN = os.getenv("CI_JOB_TOKEN")
GITLAB_API_URL = "https://gitlab.com/api/v4"
PROJECT1_ID = os.getenv("PROJECT1_ID")
PROJECT2_ID = os.getenv("PROJECT2_ID")
HARBOR_URL = os.getenv("HARBOR_URL")
HARBOR_USERNAME = os.getenv("HARBOR_USERNAME")
HARBOR_PASSWORD = os.getenv("HARBOR_PASSWORD")

if len(sys.argv) < 2:
    print("❌ Bạn cần truyền vào tên project (PROJECT_NAME)")
    sys.exit(1)

PROJECT_NAME = sys.argv[1]

# Encode basic auth
basic_auth = base64.b64encode(f"{HARBOR_USERNAME}:{HARBOR_PASSWORD}".encode()).decode()
headers = {
    "Authorization": f"Basic {basic_auth}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def project_exists(name):
    r = requests.get(f"{HARBOR_URL}/api/v2.0/projects/{name}", headers=headers)
    return r.status_code == 200

def create_project(name):
    print(f"📁 Creating Harbor project: {name}")
    data = {
        "project_name": name,
        "public": False
    }
    r = requests.post(f"{HARBOR_URL}/api/v2.0/projects", headers=headers, json=data)
    r.raise_for_status()

def create_robot_account(suffix, access_list):
    robot_name = f"robot${PROJECT_NAME.replace('-', '')}-{suffix}"
    data = {
        "name": robot_name,
        "access": access_list,
        "expires_at": 0
    }
    r = requests.post(f"{HARBOR_URL}/api/v2.0/projects/{PROJECT_NAME}/robots", headers=headers, json=data)
    r.raise_for_status()
    return r.json()

def export_variable_to_gitlab(project_id, key, value):
    print(f"🔐 Setting GitLab variable: {key} to project ID {project_id}")
    url = f"{GITLAB_API_URL}/projects/{project_id}/variables/{key}"
    data = {
        "key": key,
        "value": value,
        "masked": False,
        "protected": False
    }
    headers_gitlab = {
        "PRIVATE-TOKEN": GITLAB_TOKEN
    }
    r = requests.put(url, headers=headers_gitlab, data=data)
    if r.status_code == 404:
        r = requests.post(f"{GITLAB_API_URL}/projects/{project_id}/variables", headers=headers_gitlab, data=data)
    r.raise_for_status()

if __name__ == "__main__":
    if not project_exists(PROJECT_NAME):
        create_project(PROJECT_NAME)

    pull_robot = create_robot_account("pullonly", [
        {"resource": f"/project/{PROJECT_NAME}/repository", "action": "pull"}
    ])

    push_robot = create_robot_account("push", [
        {"resource": f"/project/{PROJECT_NAME}/repository", "action": "push"},
        {"resource": f"/project/{PROJECT_NAME}/repository", "action": "pull"}
    ])

    env_prefix = "DEV" if PROJECT_NAME.startswith("dev-") else "PROD"

    export_variable_to_gitlab(PROJECT1_ID, f"HARBOR_PROJECT_{env_prefix}", PROJECT_NAME)
    export_variable_to_gitlab(PROJECT1_ID, f"HARBOR_USER_{env_prefix}", push_robot['name'])
    export_variable_to_gitlab(PROJECT1_ID, f"HARBOR_TOKEN_{env_prefix}", push_robot['secret'])

    if env_prefix == "PROD":
        export_variable_to_gitlab(PROJECT2_ID, f"HARBOR_PULL_USER_{env_prefix}", pull_robot['name'])
        export_variable_to_gitlab(PROJECT2_ID, f"HARBOR_PULL_TOKEN_{env_prefix}", pull_robot['secret'])
    else:
        export_variable_to_gitlab(PROJECT1_ID, f"HARBOR_PULL_USER_{env_prefix}", pull_robot['name'])
        export_variable_to_gitlab(PROJECT1_ID, f"HARBOR_PULL_TOKEN_{env_prefix}", pull_robot['secret'])

    print("✅ Harbor robot accounts created and GitLab variables updated successfully.")
