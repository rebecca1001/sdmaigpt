from fastapi import APIRouter

from src.blog.api import blog_router

api_router = APIRouter()

api_router.include_router(blog_router, tags=["blog"])
