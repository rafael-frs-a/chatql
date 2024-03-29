import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from src import config
from src.api.graphql import views


schema = strawberry.Schema(
    query=views.Query, mutation=views.Mutation, subscription=views.Subscription
)
graphql_app = GraphQLRouter[object, object](schema)
graphql = FastAPI(title=config.APP_NAME)
graphql.include_router(graphql_app, prefix="/graphql")
