import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from mangum import Mangum

from back.api_boards import router as boards_router
from back.api_challenges import router as challenges_router
from back.api_task_gen import router as task_gen_router
from back.api_tasks import router as tasks_router
# Routers split by domain
from back.api_teams import router as team_router
from back.firebase_test_setup import setup_firebase_emulator, create_test_firebase_data

app = FastAPI(title="Teamwork Challenge API",
              description="API for managing teamwork challenges and tasks",
              version="1.0.0",
              debug=True)

# Include split routers
app.include_router(team_router)
app.include_router(challenges_router)
app.include_router(tasks_router)
app.include_router(boards_router)


# Hide task generators from OpenAPI
app.include_router(task_gen_router, include_in_schema=False)


@app.get("/", include_in_schema=False)
def home() -> RedirectResponse:
    return RedirectResponse(url="/docs")


handler = Mangum(app, lifespan="off")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        print("Starting in dev mode")
        setup_firebase_emulator()
        create_test_firebase_data()
        uvicorn.run(
            "back.main:app",
            reload=True,
            reload_dirs=[".", "../api_models"],
            port=8089,
        )
    else:
        uvicorn.run(
            "back.main:app",
            host="0.0.0.0",
        )

