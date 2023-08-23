import traceback
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request, status

from src.main import api_router


def create_app():
    app = FastAPI()

    async def catch_exceptions_middleware(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            print(traceback.format_exc())

            if isinstance(exc, HTTPException):
                raise exc

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": str(exc),
                    "message": "Something went wrong!",
                },
            )

    app.middleware("http")(catch_exceptions_middleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins="*",
        allow_headers=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
    )

    @app.get("/", status_code=status.HTTP_200_OK)
    def welcome_page():
        return {"message": "Hello, welcome to the Blog Generator!!"}

    app.include_router(api_router, prefix="/v1")

    return app
