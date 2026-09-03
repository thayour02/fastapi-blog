from typing import Annotated

from fastapi import APIRouter,Depends,HTTPException,status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import model
from database import Base, engine, get_db
from schema import UserCreate,UserPrivate,UserUpdate,PostResponse

router = APIRouter()





@router.get("/users", response_model=list[UserPrivate])
async def get_users(db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(model.User))
    users = result.scalars().all()
    return users
