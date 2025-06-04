from __future__ import print_function
import urllib3
import harbor_client
from harbor_client.rest import ApiException
from pprint import pprint

# 🔒 Disable SSL warning (only for self-signed certs)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =============================
# 1. CONFIG
# =============================
HARBOR_URL = "https://your-harbor-domain"
USERNAME = "admin"
PASSWORD = "your-password"
PROJECT_NAME = "xuannt9"
ROBOT_NAME = f"robot-{PROJECT_NAME}"

# =============================
# 2. Setup Harbor API client
# =============================
configuration = harbor_client.Configuration()
configuration.host = HARBOR_URL
configuration.username = USERNAME
configuration.password = PASSWORD
configuration.verify_ssl = False  # True if you have a valid certificate
api_client = harbor_client.ApiClient(configuration)

# =============================
# 3. Check and create project
# =============================
project_api = harbor_client.ProjectApi(api_client)

try:
    project = project_api.get_project(PROJECT_NAME, x_is_resource_name=True)
    print(f"✅ Project '{PROJECT_NAME}' already exists.")
except ApiException as e:
    if e.status == 404:
        print(f"📦 Project '{PROJECT_NAME}' not found. Creating it...")
        new_project = harbor_client.ProjectReq(
            project_name=PROJECT_NAME,
            metadata={"public": "false"}
        )
        try:
            project = project_api.create_project(new_project)
            print(f"✅ Project '{PROJECT_NAME}' created successfully.")
        except ApiException as ce:
            print("❌ Failed to create project:", ce)
            exit(1)
    else:
        print("❌ Failed to check project:", e)
        exit(1)

# =============================
# 4. Create Robot Account
# =============================
robot_api = harbor_client.Robotv1Api(api_client)

robot_create = harbor_client.RobotCreateV1(
    name=ROBOT_NAME,
    description=f"Robot for project {PROJECT_NAME}",
    expires_at=-1,  # Never expire
    access=[
        harbor_client.RobotAccess(
            resource=f"/project/{PROJECT_NAME}/repository",
            action="pull"
        ),
        harbor_client.RobotAccess(
            resource=f"/project/{PROJECT_NAME}/repository",
            action="push"
        )
    ]
)

try:
    robot_resp = robot_api.create_robot_v1(
        project_name_or_id=PROJECT_NAME,
        robot=robot_create,
        x_is_resource_name=True
    )
    print("✅ Robot account created successfully!")
    print("👤 Robot Username:", robot_resp.name)
    print("🔐 Robot Token:", robot_resp.secret)
except ApiException as e:
    if e.status == 409:
        print(f"⚠️ Robot account '{ROBOT_NAME}' already exists.")
    else:
        print("❌ Failed to create robot account:", e)
