from src.api.graphql import schemas
from src.api.graphql.auth import schemas as auth_schemas


class EmailClient:
    async def send_authentication_email(
        self, credentials: auth_schemas.AuthenticationCredentials, url: str
    ) -> schemas.ApiResponse[str]:
        # TODO: send URL by email
        url += f"?accessToken={credentials.accessToken}&refreshToken={credentials.refreshToken}"
        print(f"URL: {url}")
        return schemas.ApiResponse(data="Authentication email sent successfully")
