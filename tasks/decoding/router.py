from typing import Dict, Tuple, List
import random

from fastapi import APIRouter

from api_models import GenRequest, GenResponse, CheckRequest, CheckResult

router = APIRouter()

# --------------------------
# Generator Functions
# --------------------------

def get_random_sentence():
    with open("sentences.txt", "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]
    return random.choice(sentences)


def get_difficulty(request: GenRequest) -> int:
    """Determine the difficulty level based on task settings and progress"""
    task_settings = request.task_settings
    progress = request.progress

    # Default to level 1
    level = 1

    # Parse task settings if available
    if task_settings:
        settings = {}
        for setting in task_settings.split(','):
            if ':' in setting:
                key, value = setting.split(':', 1)
                settings[key.strip()] = int(value.strip())

        # Check if we should increase difficulty based on task index
        task_index = progress.task_index
        for complication, threshold in sorted(settings.items()):
            if complication.startswith('complication') and task_index >= threshold:
                level_num = int(complication.replace('complication', ''))
                level = max(level, level_num)

    # Cap at maximum level 8
    return min(level, 8)

@router.post("/gen", response_model=GenResponse)
async def generate_task(request: GenRequest):
    """Generate a new a_plus_b task"""
    level = get_difficulty(request)
    type_a = random.randint(1, level)  # Cap at available types
    type_b = random.randint(1, level)

    # Generate inputs (handles matrix size automatically)
    a, b = generate_mixed_types(type_a, type_b)

    # Create input string representation
    input_data = f"{a}\n{b}"

    # Get statement based on highest complexity type
    statement_key = f"v{level}"
    return GenResponse(
        statement_version=statement_key,
        statement=STATEMENTS[statement_key],
        score="100",
        input=input_data,
        checker_hint=get_answer(a, b, type_a, type_b)
    )


@router.get("/statements", response_model=Dict[str, str])
async def get_statements():
    """Get the task statements"""
    return STATEMENTS


@router.post("/check", response_model=CheckResult)
async def check_answer(request: CheckRequest) -> CheckResult:
    """Check the answer for an a_plus_b task"""
    try:
        # Get the expected answer from the checker hint
        expected_answer = request.checker_hint.strip()

        # Check if the answer is correct
        if request.answer.strip() == expected_answer:
            return CheckResult(status="AC", score=1.0)
        else:
            return CheckResult(
                status="WA",
                score=0.0,
                error=f"Expected {expected_answer}, got {request.answer.strip()}"
            )
    except Exception as e:
        return CheckResult(
            status="WA",
            score=0.0,
            error=f"Error processing answer: {str(e)}"
        )
