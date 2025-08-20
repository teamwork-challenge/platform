from lib2to3.btm_matcher import type_repr
from typing import Dict, Tuple, List
import random
from fastapi import APIRouter
from num2words import num2words
from numpy import base_repr

from api_models import GenRequest, GenResponse, CheckRequest, CheckResult, CheckStatus

router = APIRouter()

# Statements for the a_plus_b task
STATEMENT = "find sum of a and b"


# --------------------------
# Number Generator Functions
# --------------------------

def gen_int() -> int:
    """Generate random integer between 1 and 100"""
    return random.randint(1, 100)


def gen_random_base_number(answer: int = None) -> Tuple[str, int]:
    answer = answer or random.randint(1, 100000)
    base = random.randint(2, 16)
    return base_repr(answer, base), answer


def gen_bigint() -> Tuple[int, int]:
    answer = random.randint(-10 ** 30, 10 ** 30)
    return answer, answer


def gen_complex() -> Tuple[complex, complex]:
    """Generate random complex number with parts between 1 and 50"""
    answer = complex(random.randint(1, 50), random.randint(1, 50))
    return answer, answer


def gen_matrix(size: int = None) -> List[List[int]]:
    """Generate random square matrix of integers"""
    size = size or random.randint(2, 5)
    return [[random.randint(0, 10) for _ in range(size)] for _ in range(size)]


def gen_fib_num(answer: int = None) -> Tuple[str, int]:
    """Generate random number in Fibonacci numeral system (marked with F)"""

    def decimal_to_fib(n: int) -> str:
        fibs = []
        a, b = 1, 2
        while a <= n:
            fibs.append(a)
            a, b = b, a + b
        res = []
        for f in reversed(fibs):
            if n >= f:
                res.append('1')
                n -= f
            else:
                res.append('0')
        return ''.join(res) or '0'

    answer = answer or random.randint(1, 10000)
    return decimal_to_fib(answer) + "_F", answer


def gen_roman_num(answer: int = None) -> Tuple[str, int]:
    """Generate random Roman numeral between 1 and 10000"""

    def int_to_roman(n: int) -> str:
        val = [
            (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
            (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
            (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
        ]
        res = []
        for num, sym in val:
            while n >= num:
                res.append(sym)
                n -= num
        return ''.join(res)

    answer = answer or random.randint(1, 4999)
    return int_to_roman(answer), answer


def gen_word_num(answer: int = None) -> Tuple[str, int]:
    """Generate random number expressed in words (e.g., 'two hundred seventy-two million')"""
    # Generate numbers up to 1 trillion (1,000,000,000,000)
    answer = answer or random.randint(1, 10 ** 12)

    # Convert to words with proper formatting
    return num2words(answer).replace(" and ", " "), answer  # Remove "and" for cleaner format


# --------------------------
# Level Generator Functions
# --------------------------
# Generate each type independently
generators = {
    1: gen_int,
    2: gen_random_base_number,
    3: gen_bigint,
    4: gen_complex,
    5: gen_matrix,
    6: gen_fib_num,
    7: gen_roman_num,
    8: gen_word_num
}


def randomize_matrix_representation(matrix, level_cap):
    for i in range(len(matrix)):
        for j in range(len(matrix)):
            gen = random.choice([1, 2, 6, 7])
            if type <= level_cap:
                matrix[i][j] = generators[gen](matrix[i][j])
    return matrix


def generate_mixed_types(type_a: int, type_b: int) -> Tuple:
    """Generate inputs of different types, handling matrices specially"""
    if type_a == 5:
        if type_b == 5:
            size = random.randint(2, 5)
            a = gen_matrix(size)
            b = gen_matrix(size)
            answer = str([[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))])
            return a, b, answer
        else:
            return generators[type_a](), generators[type_b]()[0], "Incompatible types for addition"
    if type_b == 5:
        return generators[type_a]()[0], generators[type_b](), "Incompatible types for addition"
    a, a_dec = generators[type_a]()
    b, b_dec = generators[type_b]()
    if isinstance(a_dec, complex) or isinstance(b_dec, complex):
        a_dec = complex(a_dec)
        b_dec = complex(b_dec)
    return a, b, str(a_dec + b_dec)


# --------------------------
# Core Application Logic
# --------------------------


# TODO: Create a standard task-gen-settings in the format "1-7" which means: "uniformly distribute task-levels from level1 to level7. Use it in all task_gens if possible.
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
    a, b, hint_data = generate_mixed_types(type_a, type_b)

    # Create input string representation
    input_a = f"{a}"
    input_b = f"{b}"
    if type_a == 5:
        input_a = '\n'.join([' '.join(i) for i in a])
    if type_b == 5:
        input_b = '\n'.join([' '.join(i) for i in a])
    input_data = input_a + '\n' + input_b

    # Get statement based on highest complexity type
    statement_key = f"v{level}"
    return GenResponse(
        statement_version=statement_key,
        statement=STATEMENT,
        input=input_data,
        checker_hint=hint_data
    )


@router.get("/statements", response_model=Dict[str, str])
async def get_statements():
    """Get the task statements"""
    return STATEMENT


@router.post("/check", response_model=CheckResult)
async def check_answer(request: CheckRequest) -> CheckResult:
    """Check the answer for an a_plus_b task"""
    # Get the expected answer from the checker hint
    expected_answer = request.checker_hint.strip()

    # Check if the answer is correct
    if request.answer.strip() == expected_answer:
        return CheckResult(status=CheckStatus.ACCEPTED, score=1.0)
    else:
        error_data = f"Expected [{expected_answer}], got [{request.answer.strip()}]"
        if '_F' in request.input:
            error_data += f"\n_F stands for Fibonacci numeral system"
        return CheckResult(
            status=CheckStatus.WRONG_ANSWER,
            score=0.0,
            error=error_data
        )
