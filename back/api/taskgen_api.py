from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import APIKeyHeader

from api_models import GenRequest, GenResponse, CheckRequest, CheckResult, CheckStatus

# Internal task generators for tests
router = APIRouter(prefix="/task_gen", tags=["TaskGen"])  # hidden from OpenAPI via include_in_schema in main

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def validate_api_key(api_key: Annotated[str, Depends(API_KEY_HEADER)]) -> str:
    if api_key != "secret":
        raise HTTPException(status_code=403, detail="Invalid API key")
    # mypy: api_key is str | None; reaching here implies api_key == "secret" and thus not None.
    return api_key or "secret"


@router.post("/a_plus_b/gen", dependencies=[Depends(validate_api_key)])
def a_plus_b_gen(req: GenRequest) -> GenResponse:
    a, b = 1, 2
    statement = "Given two integers a and b, output a + b."
    input_text = f"{a} {b}"
    checker_hint = str(a + b)
    return GenResponse(
        statement_version="1.0",
        statement=statement,
        input=input_text,
        checker_hint=checker_hint
    )


@router.post("/a_plus_b/check", dependencies=[Depends(validate_api_key)])
def a_plus_b_check(req: CheckRequest) -> list[CheckResult]:
    parts = (req.input or "").strip().split()
    if len(parts) != 2:
        return [CheckResult(status=CheckStatus.WRONG_ANSWER, error="Invalid input format")]
    a, b = int(parts[0]), int(parts[1])
    correct = str(a + b)
    if (req.answer or "").strip() == correct:
        return [CheckResult(status=CheckStatus.ACCEPTED, score=1.0)]
    else:
        return [CheckResult(status=CheckStatus.WRONG_ANSWER, error="Wrong answer", score=0.0)]
