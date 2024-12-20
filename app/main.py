"""main"""
import traceback

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse

from .routes import api

app = FastAPI()


@app.exception_handler(Exception)
async def internal_server_error_handler(_request: Request, exc: Exception):
    """internal server error"""
    stack_trace = traceback.format_exc()

    error_line = stack_trace.splitlines()[-1]

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error": str(exc),
            "error_line": error_line,
            "stack_trace": stack_trace,
        },
    )


app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(api)
