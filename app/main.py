from fastapi import FastAPI

from .errors import register_exception_handlers
from .routers import tasks

app = FastAPI(title="Task API", version="1.0.0")
register_exception_handlers(app)
app.include_router(tasks.router)
