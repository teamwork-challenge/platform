import json
import os
import boto3
from fastapi import HTTPException, Depends
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def validate_api_key(x_api_key: str = Depends(API_KEY_HEADER)) -> str:
    """
    Validate the API key against the one stored in AWS Secrets Manager.
    """
    if os.environ["STAGE"] == "local":
        return "local_api_key"
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key is required")
    secret_name = "generator-client-keys"
    region_name = "eu-north-1"
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )
    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
        keys = json.loads(secret) # { "api_key": "owner" }
        print(x_api_key, keys, x_api_key not in keys.values())
        if x_api_key not in keys.values():
            raise HTTPException(status_code=401, detail="Invalid API key")
    else:
        raise HTTPException(status_code=500, detail="Could not retrieve API key from Secrets Manager")
    return x_api_key