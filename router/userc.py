from typing import Annotated

from fastapi import APIRouter,Depends,HTTPException,status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import model
from database import Base, engine, get_db
from schema import UserCreate,UserResponse,UserUpdate,PostResponse

router = APIRouter()


## create_user
@router.post(
        "",
        response_model=UserResponse,
        status_code=status.HTTP_201_CREATED,
    )
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(model.User).where(model.User.username == user.username),
    )
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    result = await db.execute(
        select(model.User).where(model.User.email == user.email),
    )
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = model.User(
        username=user.username,
        email=user.email,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


## get_user
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(model.User).where(model.User.id == user_id))
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


## get_user_posts
@router.get("/{user_id}/post", response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(model.User).where(model.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    result = await db.execute(
        select(model.Post)
        .options(selectinload(model.Post.author))
        .where(model.Post.user_id == user_id),
    )
    posts = result.scalars().all()
    return posts


## update_user
@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
        user_id: int,
        user_update: UserUpdate,
        db: Annotated[AsyncSession, Depends(get_db)],
    ):
    result = await db.execute(select(model.User).where(model.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user_update.username is not None and user_update.username != user.username:
        result = await db.execute(
            select(model.User).where(model.User.username == user_update.username),
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )
    if user_update.email is not None and user_update.email != user.email:
        result = await db.execute(
            select(model.User).where(model.User.email == user_update.email),
        )
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    if user_update.username is not None:
        user.username = user_update.username
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    await db.commit()
    await db.refresh(user)
    return user


## delete_user
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(model.User).where(model.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await db.delete(user)
    await db.commit()

@router.get("", include_in_schema=False)
async def get_users(db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(model.User).options(selectinload(model.User.posts)))
    users = result.scalars().all()
    return users
