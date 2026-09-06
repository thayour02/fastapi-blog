from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI,Request,HTTPException,status,Depends
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import model
from database import engine, get_db
from router import userc,postc,admin
from config import settings



@asynccontextmanager
async def lifespan(_app:FastAPI):
    yield
    #shutdown
    await engine.dispose()


app = FastAPI(lifespan=lifespan)



app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

template = Jinja2Templates(directory="templates")

app.include_router(admin.router, prefix='/admin', tags=["admin"])
app.include_router(userc.router, prefix="/api/user", tags=["users"])
app.include_router(postc.router, prefix="/api/post", tags=["posts"])

@app.get("/", include_in_schema=False)
async def home(request: Request, db:Annotated[AsyncSession, Depends(get_db)]):
    count_result = await db.execute(select(func.count()).select_from(model.Post))
    total = count_result.scalar() or 0

    result = await db.execute(select(model.Post)
    .options(selectinload(model.Post.author))
    .order_by(model.Post.date_posted.desc())
    .limit(settings.posts_per_page)
    )


    posts = result.scalars().all()

    has_more = len(posts) < total
    return template.TemplateResponse(request,
    "home.html", 
    {"posts":posts, "title":"Home",
    "limit":settings.posts_per_page, 
    "has_more":has_more})


## user_posts_page
@app.get("/user/{user_id}/post", include_in_schema=False, name="get_user_posts_page")
async def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(model.User).where(model.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    count_result = await db.execute(
        select(func.count())
        .select_from(model.Post)
        .where(model.Post.user_id == user_id),
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(model.Post)
        .options(selectinload(model.Post.author))
        .where(model.Post.user_id == user_id)
        .order_by(model.Post.date_posted.desc())
        .limit(settings.posts_per_page),
    )
    posts = result.scalars().all()

    has_more = len(posts) < total

    return template.TemplateResponse(
        request,
        "user_post.html",
        {
            "posts": posts,
            "user": user,
            "title": f"{user.username}'s Posts",
            "limit": settings.posts_per_page,
            "has_more": has_more,
        },
    )
## get_post (HTML page)
@app.get('/post/{post_id}', include_in_schema=False, name="get_post")
async def get_post(request: Request, post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(model.Post)
        .options(selectinload(model.Post.author))
        .where(model.Post.id == post_id),
    )
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    title = post.title[:50]
    return template.TemplateResponse(request, "post.html", {"post": post, "title": title})


## login_page
@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return template.TemplateResponse(request, "login.html", {"title": "Login"})


## register_page
@app.get("/register", include_in_schema=False)
async def register_page(request: Request):
    return template.TemplateResponse(request, "register.html", {"title": "Register"})


## Account_page
@app.get("/account", include_in_schema=False)
async def account_page(request: Request):
    return template.TemplateResponse(request, "account.html", {"title": "Account"})

@app.get("/forgot-password", include_in_schema=False)
async def forgot_password_page(request: Request):
    return template.TemplateResponse(
        request,
        "forgot_pass.html",
        {"title": "Forgot Password"},
    )


@app.get("/reset-password", include_in_schema=False)
async def reset_password_page(request: Request):
    response = template.TemplateResponse(
        request,
        "reset_pass.html",
        {"title": "Reset Password"},
    )
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


## StarletteHTTPException Handler
@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return await http_exception_handler(
            request,
            exception,
        )
    return template.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )



### RequestValidationError Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request, exception)
    return template.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
