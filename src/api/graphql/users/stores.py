from src.db.models.user import User


class UserStore:
    async def get_or_create_user(self, email: str) -> User:
        db_user = await User.find_one({"email": {"$regex": email, "$options": "i"}})

        if db_user:
            return db_user

        new_user = User(email=email)
        created_user: User = await new_user.save()
        return created_user

    async def get_users(self) -> list[User]:
        return await User.find().sort("email").to_list()
