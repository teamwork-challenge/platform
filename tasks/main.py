import importlib
import os
from fastapi import FastAPI, Depends, Security
from mangum import Mangum
from auth import validate_api_key

generators = ['right_time', 'a_plus_b']

app = FastAPI(title="Teamwork Challenge Task Generators", dependencies=[Depends(validate_api_key)])

def register_generators():
    for generator in generators:
        module = importlib.import_module(f"{generator}.router")
        if hasattr(module, "router"):
            app.include_router(module.router, prefix=f"/{generator}", tags=[generator])

register_generators()

# AWS Lambda handler
handler = Mangum(app)

if __name__ == "__main__":
    # For local development, set STAGE=local to bypass API key validation
    os.environ["STAGE"] = "local"

    import uvicorn
    uvicorn.run(
        'main:app',
        reload=True,
        reload_dirs=[".", "../api_models"],
        port=8002,
    )
