from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import events_router

app = FastAPI(title="API Events - first step")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "message": "API Event - First Step"}


app.include_router(events_router)
