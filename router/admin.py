from typing import Annotated

from fastapi import APIRouter,Depends,HTTPException,status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import model
from database import Base, engine, get_db
from schema import UserCreate,UserResponse,UserUpdate,PostResponse

router = APIRouter()





@router.get("", include_in_schema=False)
async def get_users(db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(model.User).options(selectinload(model.User.posts)))
    users = result.scalars().all()
    return users
