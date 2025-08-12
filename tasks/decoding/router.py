from math import gcd
from typing import Dict, Tuple, List
import random
import heapq
from collections import Counter

from fastapi import APIRouter

from api_models import GenRequest, GenResponse, CheckRequest, CheckResult

router = APIRouter()
STATEMENTS = {
    "v1": "",
    "v2": "",
    "v3": "",
    "v4": "",
    "v5": "",
    "v6": "",
    "v7": "",
    "v8": "",
}

# --------------------------
# Generator Functions
# --------------------------
MORSE_CODE = {
    'a': '.-', 'b': '-...', 'c': '-.-.', 'd': '-..',
    'e': '.', 'f': '..-.', 'g': '--.', 'h': '....',
    'i': '..', 'j': '.---', 'k': '-.-', 'l': '.-..',
    'm': '--', 'n': '-.', 'o': '---', 'p': '.--.',
    'q': '--.-', 'r': '.-.', 's': '...', 't': '-',
    'u': '..-', 'v': '...-', 'w': '.--', 'x': '-..-',
    'y': '-.--', 'z': '--..'
}


def get_random_sentence():
    with open("sentences.txt", "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]
    return random.choice(sentences)


def generate_caesar_cipher(sentence: str, shift: int = 1) -> str:
    result = ''
    for char in sentence:
        if char.isalpha():
            result += (chr((ord(char) - ord('a') + shift) % 26 + ord('a')))
        else:
            result += char
    return result


def generate_morse_code(sentence: str) -> str:
    return ' '.join(MORSE_CODE.get(char, '') for char in sentence if char.isalnum() or char == ' ')

def generate_affine_cipher(sentence: str) -> Tuple[str, str]:
    coprimes = [n for n in range(1, 26, 2) if gcd(n, 26) == 1]
    a = random.choice(coprimes)
    b = random.randint(0, 1000)
    result = ''.join([chr(((a * (ord(ch) - ord('a')) + b) % 26) + ord('a')) if ch.isalpha() else ch for ch in sentence])
    return result, f"f(x) = ({a} * x + {b}) mod 26"

def is_binary_string(s: str) -> bool:
    return all(ch in '01' for ch in s)

def is_prefix_free(codes: List[str]) -> bool:
    # Sort codes by length, then check if any code is prefix of another
    sorted_codes = sorted(codes, key=len)
    for i in range(len(sorted_codes)):
        for j in range(i+1, len(sorted_codes)):
            if sorted_codes[j].startswith(sorted_codes[i]):
                return False
    return True

def huffman_bit_length(sentence: str) -> int:
    freq = Counter(sentence)
    # Special case: only one unique character
    if len(freq) == 1:
        return len(sentence)  # all characters use 1 bit
    heap = list(freq.values())
    heapq.heapify(heap)
    total_bits = 0
    while len(heap) > 1:
        f1 = heapq.heappop(heap)
        f2 = heapq.heappop(heap)
        total_bits += f1 + f2
        heapq.heappush(heap, f1 + f2)
    return total_bits


def check_student_answer_huffman(minimal_bits_number: int, student_answer: str) -> Tuple[bool, str]:
    lines = student_answer.strip().split('\n')
    try:
        n = int(lines[0])
    except:
        return False, "First line must be integer number of encoded symbols N"

    if n > 26:
        return False, f"Too many encoded symbols: {n}"

    if len(lines) != n + 2:
        return False, f"Expected {n} code lines + encoded text, got {len(lines)-1}"

    char_code_lines = lines[1:1+n]
    encoded_text = lines[-1]

    # Parse codes
    codes = {}
    for line in char_code_lines:
        if len(line.strip().split()) != 2:
            return False, f"Invalid code line format: '{line}'. Expected format: 'a 1001\nb 11\n..."
        ch, code = line.strip().split()
        if len(ch) != 1 or not ch.isalpha() or not ch.islower():
            return False, f"Invalid character: '{ch}'"
        if not is_binary_string(code):
            return False, f"Code for character '{ch}' is not binary: '{code}'"
        if ch in codes:
            return False, f"Duplicate character code for '{ch}'"
        codes[ch] = code

    # Check all codes are prefix free
    if not is_prefix_free(list(codes.values())):
        return False, "Codes are not prefix free"

    # Check encoded text is binary only
    if not is_binary_string(encoded_text):
        return False, "Encoded text contains non-binary characters"

    #TODO
    # Compute total bits used by student code
    # Compute minimal bits by Huffman

    return True, "Code is binary, prefix-free, and optimal"


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
