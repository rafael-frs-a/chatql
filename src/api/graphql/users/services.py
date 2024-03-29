from src.api.graphql import schemas
from src.api.graphql.users import schemas as user_schemas
from src.api.graphql.users import stores


class UserService:
    def __init__(self) -> None:
        self.store = stores.UserStore()

    async def get_users(self) -> schemas.ApiResponse[list[user_schemas.User]]:
        users = await self.store.get_users()
        data = [user_schemas.User(user) for user in users]
        return schemas.ApiResponse(data=data)
