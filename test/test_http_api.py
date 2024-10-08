from satisfactory_api_client import SatisfactoryAPI
from dotenv import load_dotenv
import os
from satisfactory_api_client.data import MinimumPrivilegeLevel

load_dotenv()

api = SatisfactoryAPI(host=os.getenv("SERVER_ADDRESS"), port=os.getenv("SERVER_PORT"))

response = api.password_login(
    MinimumPrivilegeLevel.ADMINISTRATOR, password=os.getenv("ADMIN_PASSWORD")
)

response = api.health_check()
print(response.data)

# Get server state
response = api.query_server_state()
print(response.data)

# Get server options
response = api.get_server_options()
print(response.data)
