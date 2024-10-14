from asgiref.sync import sync_to_async
from satisfactory_api_client import SatisfactoryAPI
from satisfactory_api_client.data import MinimumPrivilegeLevel


class HttpApi:
    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port
        self.api = SatisfactoryAPI(host=self.address, port=self.port)

    async def login(self, password: str):
        await sync_to_async(self.api.password_login)(
            MinimumPrivilegeLevel.ADMINISTRATOR, password=password
        )

    async def health_check(self):
        return await sync_to_async(self.api.health_check)()

    async def query_server_state(self):
        return await sync_to_async(self.api.query_server_state)()

    async def get_server_options(self):
        return await sync_to_async(self.api.get_server_options)()
