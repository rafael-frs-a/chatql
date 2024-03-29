import strawberry
from src.api.graphql import schemas
from src.api.graphql.auth import views as auth_views
from src.api.graphql.users import views as user_views
from src.api.graphql.messages import views as message_views


@strawberry.type
class Query(user_views.Query, message_views.Query):
    @strawberry.field
    def health_check(self) -> schemas.ApiResponse[None]:
        return schemas.ApiResponse()


@strawberry.type
class Mutation(auth_views.Mutation, message_views.Mutation):
    pass


@strawberry.type
class Subscription(message_views.Subscription):
    pass
