import os
import requests
import sys

# --- Environment Variables Required ---
HARBOR_URL = os.getenv("HARBOR_URL")  # ví dụ: https://harbor.mycorp.com
HARBOR_USERNAME = os.getenv("HARBOR_USERNAME")  # admin hoặc tài khoản có quyền
HARBOR_PASSWORD = os.getenv("HARBOR_PASSWORD")
PROJECT_NAME = os.getenv("HARBOR_PROJECT")  # ví dụ: my-app-service
ROBOT_NAME = os.getenv("HARBOR_ROBOT_NAME")  # ví dụ: robot-my-app-service

# --- Optional Naming Convention ---
ROBOT_DESCRIPTION = f"Robot account for project: {PROJECT_NAME}"

# Create HTTP session
session = requests.Session()
session.auth = (HARBOR_USERNAME, HARBOR_PASSWORD)
session.headers.update({"Content-Type": "application/json"})

def project_exists(name):
    url = f"{HARBOR_URL}/api/v2.0/projects/{name}"
    response = session.get(url)
    return response.status_code == 200

def create_project(name):
    print(f"🔧 Creating project: {name}")
    url = f"{HARBOR_URL}/api/v2.0/projects"
    payload = {"project_name": name, "public": False}
    response = session.post(url, json=payload)
    if response.status_code == 201:
        print("✅ Project created.")
    elif response.status_code == 409:
        print("⚠️  Project already exists.")
    else:
        print(f"❌ Failed to create project: {response.status_code} {response.text}")
        sys.exit(1)

def create_robot_account(project, robot_name):
    print(f"🔧 Creating robot account: {robot_name}")
    url = f"{HARBOR_URL}/api/v2.0/projects/{project}/robots"
    payload = {
        "name": robot_name,
        "description": ROBOT_DESCRIPTION,
        "expires_at": 0,  # never expire
        "access": [
            {
                "resource": f"/project/{project}/repository",
                "action": "push"
            },
            {
                "resource": f"/project/{project}/repository",
                "action": "pull"
            }
        ]
    }

    response = session.post(url, json=payload)
    if response.status_code == 201:
        data = response.json()
        print("✅ Robot account created.")
        print("ROBOT_USERNAME:", data["name"])
        print("ROBOT_TOKEN:", data["secret"])
        return data
    elif response.status_code == 409:
        print("⚠️  Robot account already exists. Please delete or rename.")
    else:
        print(f"❌ Failed to create robot account: {response.status_code} {response.text}")
        sys.exit(1)

# --- Main execution ---
if __name__ == "__main__":
    if not project_exists(PROJECT_NAME):
        create_project(PROJECT_NAME)
    else:
        print("✅ Project already exists.")

    robot = create_robot_account(PROJECT_NAME, ROBOT_NAME)
