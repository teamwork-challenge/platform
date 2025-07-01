from typing import Dict
from fastapi import APIRouter
import random
from api_models import GenRequest, GenResponse, CheckRequest, CheckResult

router = APIRouter()

# Statements for the right_time task
STATEMENTS = {
    "v1": "Submit your answer exactly at the second specified in the input. The input contains a single integer - the target second."
}

@router.get("/statements", response_model=Dict[str, str])
async def get_statements():
    """Get the task statements"""
    return STATEMENTS

@router.post("/gen", response_model=GenResponse)
async def generate_task(request: GenRequest):
    """Generate a new right_time task"""
    # Generate a random target second (between 5 and 30 seconds from now)
    target_second = random.randint(5, 30)

    # Create the input string
    input_data = str(target_second)

    return GenResponse(
        statement_version="v1",
        score="100",
        input=input_data,
        checker_hint=input_data  # Store the target second as a hint for the checker
    )

@router.post("/check")
async def check_answer(request: CheckRequest):
    """Check the answer for a right_time task"""
    try:
        # Get the target second from the input
        target_second = int(request.input.strip())

        # The answer doesn't matter, only the timing
        # In a real implementation, we would check the submission timestamp
        # For this skeleton, we'll simulate it by accepting any answer
        # and assuming the timing is correct

        # In a real implementation, we would do something like:
        # submission_second = get_submission_second_from_timestamp()
        # if submission_second == target_second:
        #     return [CheckResult(status="AC", score=1.0)]
        # else:
        #     return [CheckResult(
        #         status="WA",
        #         score=0.0,
        #         error=f"Expected submission at second {target_second}, got {submission_second}"
        #     )]

        # For this skeleton, we'll just return success
        return [CheckResult(status="AC", score=1.0)]
    except Exception as e:
        return [CheckResult(
            status="WA",
            score=0.0,
            error=f"Error processing answer: {str(e)}"
        )]
