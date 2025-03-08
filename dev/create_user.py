#!/usr/bin/env python3

from dbcalm.data.model.user import User
from dbcalm.data.repository.user import UserRepository


def create_user(username: str, password: str) -> None:
    """Create a new user with hashed password"""
    user = User(username=username, password=password)
    user_repo = UserRepository()
    created_user = user_repo.create(user)
    print(f"User '{created_user.username}' created successfully")
    print("Password has been hashed using bcrypt")


if __name__ == "__main__":
    create_user("test", "test")
