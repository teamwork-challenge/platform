from typing import Dict, Tuple, List
import random
from fastapi import APIRouter
from num2words import num2words
from word2number import w2n

from api_models import GenRequest, GenResponse, CheckRequest, CheckResult

router = APIRouter()

# Statements for the a_plus_b task
STATEMENTS = {
    "v1": "Given two numbers a and b, find their sum a + b.",
    "v2": "Given two numbers a and b, find their sum a + b.",
    "v3": "Given two numbers a and b, find their sum a + b.",
    "v4": "Given two matrices a and b, find their sum a + b.",
    "v5": "Given two matrices a and b, find their sum a + b.",
    "v6": "Given two matrices a and b, find their sum a + b. Numbers in Fibonacci numeral system could also appear.",
    "v7": "Given two matrices a and b, find their sum a + b.",
    "v8": "Given two matrices a and b, find their sum a + b.",
}


# --------------------------
# Number Generator Functions
# --------------------------

def gen_int() -> int:
    """Generate random integer between 1 and 100"""
    return random.randint(1, 100)


def gen_base5() -> str:
    """Generate random base-5 integers (e.g., '342_5')"""
    digits = random.randint(1, 10)  # Max 10-digit base-5 numbers
    num = ''.join(random.choice('01234') for _ in range(digits)).lstrip('0')
    return f"{num}_5"


def gen_bigint() -> int:
    return random.randint(-10 ** 30, 10 ** 30)


def gen_complex() -> complex:
    """Generate random complex number with parts between 1 and 50"""
    return complex(random.randint(1, 50), random.randint(1, 50))


def gen_matrix(size: int = None) -> List[List[int]]:
    """Generate random square matrix of integers"""
    size = size or random.randint(2, 5)
    return [[random.randint(0, 10) for _ in range(size)] for _ in range(size)]


def gen_fib_num() -> str:
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

    return decimal_to_fib(random.randint(1, 10000)) + "F"


def gen_roman_num() -> str:
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

    return int_to_roman(random.randint(1, 4999))

def gen_word_num() -> Tuple:
    """Generate random number expressed in words (e.g., 'two hundred seventy-two million')"""
    # Generate numbers up to 1 trillion (1,000,000,000,000)
    num = random.randint(1, 10 ** 12)

    # Convert to words with proper formatting
    return num2words(num).replace(" and ", " "), num  # Remove "and" for cleaner format
# --------------------------
# Level Generator Functions
# --------------------------

def generate_mixed_types(type_a: int, type_b: int) -> Tuple:
    """Generate inputs of different types, handling matrices specially"""
    # If both are matrices, ensure same size
    if (type_a == 5 or type_b == 5) and random.randint(1, 2) == 1:
        type_b = type_a = 5
    if type_a == 5 and type_b == 5:
        size = random.randint(2, 5)
        return gen_matrix(size), gen_matrix(size)

    # Generate each type independently
    generators = {
        1: gen_int,
        2: gen_base5,
        3: gen_bigint,
        4: gen_complex,
        5: gen_matrix,
        6: gen_fib_num,
        7: gen_roman_num,
        8: gen_word_num
    }

    return generators[type_a](), generators[type_b]()


# --------------------------
# Core Application Logic
# --------------------------

def convert_to_decimal(x, type_x):
    if type_x == 2:  # Base-5 to decimal
        return int(x.rstrip('_5'), 5)
    elif type_x == 6:  # Fibonacci
        s = x.rstrip('F')
        fibs = [1, 2]
        while len(fibs) < len(s):
            fibs.append(fibs[-1] + fibs[-2])
        return sum(int(c) * fib for c, fib in zip(reversed(s), fibs))
    elif type_x == 7:  # Roman
        roman = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        s = x  # The input is the Roman numeral string
        total = 0
        prev_value = 0
        for c in reversed(s):
            curr_value = roman[c]
            if curr_value < prev_value:
                total -= curr_value
            else:
                total += curr_value
            prev_value = curr_value
        return total
    elif type_x == 8:  # Word number
        return x[1]
    return x


def get_answer(a, b, type_a: int, type_b: int, ) -> str:
    """Calculate the correct answer based on input types, returning full-precision string"""
    # Handle matrix operations

    if type_a == 5 and type_b == 5:
        return str([[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))])

    # Convert special number systems to decimal first
    a_dec = convert_to_decimal(a, type_a)
    b_dec = convert_to_decimal(b, type_b)
    if (type_a == 5) != (type_b == 5):
        return "Incompatible types for addition"
    if isinstance(a_dec, complex) or isinstance(b_dec, complex):
        a_dec = complex(a_dec)
        b_dec = complex(b_dec)
    return str(a_dec + b_dec)


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
