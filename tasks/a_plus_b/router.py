from typing import Dict

from fastapi import APIRouter
import random
from api_models import GenRequest, GenResponse, CheckRequest, CheckResult

router = APIRouter()

# Statements for the a_plus_b task
STATEMENTS = {
    "v1": "Given two integers a and b, find their sum a + b."
}

@router.get("/statements", response_model=Dict[str, str])
async def get_statements():
    """Get the task statements"""
    return STATEMENTS

@router.post("/gen", response_model=GenResponse)
async def generate_task(request: GenRequest):
    """Generate a new a_plus_b task"""
    # Generate two random integers
    a = random.randint(1, 100)
    b = random.randint(1, 100)

    # Create the input string
    input_data = f"{a} {b}"

    # The expected answer is a + b
    expected_answer = a + b

    return GenResponse(
        statement_version="v1",
        statement=STATEMENTS["v1"],
        score="100",
        input=input_data,
        checker_hint=str(expected_answer)  # Store the expected answer as a hint for the checker
    )

@router.post("/check", response_model=CheckResult)
async def check_answer(request: CheckRequest) -> CheckResult:
    """Check the answer for an a_plus_b task"""
    try:
        # Parse the input to get the two numbers
        a, b = map(int, request.input.strip().split())

        # Parse the user's answer
        user_answer = int(request.answer.strip())

        # Get the expected answer from the checker hint
        expected_answer = int(request.checker_hint.strip())

        # Check if the answer is correct
        if user_answer == expected_answer:
            return CheckResult(status="AC", score=1.0)
        else:
            return CheckResult(
                status="WA",
                score=0.0,
                error=f"Expected {expected_answer}, got {user_answer}"
            )
    except Exception as e:
        return CheckResult(
            status="WA",
            score=0.0,
            error=f"Error processing answer: {str(e)}"
        )
