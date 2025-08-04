import random
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple, cast
from zoneinfo import ZoneInfo

from dateutil import parser  # type: ignore[import-untyped]
from dateutil.relativedelta import relativedelta  # type: ignore[import-untyped]
from fastapi import APIRouter

from api_models import GenRequest, GenResponse, CheckRequest, CheckResult, CheckStatus

router = APIRouter()

# Statements for the right_time task
STATEMENTS = {
    "v1": "Send the answer back exactly in the moment of time, specified in the task input. Time is always 1 minute in the future. Time is given as string in the format '2025-07-02T15:04:05+02:00' (ISO 8601 format).",
    "v2": "Send the answer back exactly in the moment of time, specified in the task input. Time is in the range of 1-20 minutes in the future. Time is given as string in the format '2025-07-02T15:04:05+02:00' (ISO 8601 format).",
    "v3": "Send the answer back exactly in the moment of time, specified in the task input. Time is in the range of 1-20 minutes in the future. Time is given in specified timezone. Timezones: CEST, CET, MSK, UTC.",
    "v4": "Send the answer back exactly in the moment of time, specified in the task input. Time is in the range of 1 minute — 2 hours in the future. Time is given in strange timezones with a no whole shift (e.g., UTC+05:30, UTC+09:30).",
    "v5": "Send the answer back exactly in the moment of time, specified in the task input. Time is given in one of the formats: ISO 8601, RFC 2822, Unix timestamp, or duration format.",
    "v6": "Send the answer back exactly in the moment of time, specified in the task input. Time is given as a summation of the time and duration.",
    "v7": "Send the answer back exactly in the moment of time, specified in the task input. Time is given as an expression including time, duration with summation and subtraction.",
    "v8": "Send the answer back exactly in the moment of time, specified in the task input. Time is given in natural language."
}

# Timezone mappings
TIMEZONES = {
    "CEST": "Europe/Paris",
    "CET": "Europe/Paris",
    "MSK": "Europe/Moscow",
    "UTC": "UTC",
    "NST": "America/St_Johns",      # UTC-03:30
    "IRST": "Asia/Tehran",          # UTC+03:30
    "AFT": "Asia/Kabul",            # UTC+04:30
    "IST": "Asia/Kolkata",          # UTC+05:30
    "NPT": "Asia/Kathmandu",        # UTC+05:45
    "MMT": "Asia/Rangoon",          # UTC+06:30
    "ACWST": "Australia/Eucla",     # UTC+08:45
    "ACST": "Australia/Darwin",     # UTC+09:30
    "LHST": "Australia/Lord_Howe",  # UTC+10:30
    "CHAST": "Pacific/Chatham"      # UTC+12:45
}

def get_current_time() -> datetime:
    """Get the current time in UTC timezone"""
    return datetime.now(timezone.utc)

def format_iso_time(dt: datetime) -> str:
    """Format a datetime object to ISO 8601 format with proper timezone formatting"""
    time_str = dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    # Format timezone part from +0000 to +00:00
    return time_str[:-2] + ":" + time_str[-2:]

def format_rfc_time(dt: datetime) -> str:
    """Format a datetime object to RFC 2822 format with proper timezone formatting"""
    time_str = dt.strftime("%a, %d %b %Y %H:%M:%S %z")
    return time_str[:-2] + ":" + time_str[-2:]

def add_time_delta(dt: datetime, minutes: int = 0, hours: int = 0, seconds: int = 0) -> datetime:
    """Add a time delta to a datetime object"""
    return dt + timedelta(minutes=minutes, hours=hours, seconds=seconds)

def get_timezone(timezone_name: str) -> ZoneInfo:
    """Get a timezone object from a timezone name"""
    return ZoneInfo(TIMEZONES[timezone_name])

def get_difficulty_level(request: GenRequest) -> int:
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

def generate_level_1() -> Tuple[datetime, str]:
    """Generate time for level 1: Time is always 1 minute in the future"""
    now = get_current_time()
    future_time = add_time_delta(now, minutes=1)
    time_str = format_iso_time(future_time)
    return future_time, time_str

def generate_level_2() -> Tuple[datetime, str]:
    """Generate time for level 2: Time is in the range of 1-20 minutes in the future"""
    now = get_current_time()
    minutes = random.randint(1, 20)
    future_time = add_time_delta(now, minutes=minutes)
    time_str = format_iso_time(future_time)
    return future_time, time_str

def generate_level_3() -> Tuple[datetime, str]:
    """Generate time for level 3: Time with specified timezone"""
    now = get_current_time()
    minutes = random.randint(1, 20)
    timezone_name = random.choice(["CEST", "CET", "MSK", "UTC"])
    timezone = get_timezone(timezone_name)
    future_time = now.astimezone(timezone) + timedelta(minutes=minutes)
    time_str = f"{future_time.strftime('%Y-%m-%dT%H:%M:%S')} {timezone_name}"
    return future_time, time_str

def generate_level_4() -> Tuple[datetime, str]:
    """Generate time for level 4: Time with strange timezones"""
    now = get_current_time()
    minutes = random.randint(1, 120)  # 1 minute to 2 hours
    strange_timezones = ["NST", "IRST", "AFT", "IST", "NPT", "MMT", "ACWST", "ACST", "LHST", "CHAST"]
    timezone_name = random.choice(strange_timezones)
    timezone = get_timezone(timezone_name)
    future_time = now.astimezone(timezone) + timedelta(minutes=minutes)
    time_str = f"{future_time.strftime('%Y-%m-%dT%H:%M:%S')} {timezone_name}"
    return future_time, time_str

def generate_level_5() -> Tuple[datetime, str]:
    """Generate time for level 5: Different time formats"""
    now = get_current_time()
    minutes = random.randint(1, 120)
    future_time = add_time_delta(now, minutes=minutes)

    format_type = random.randint(1, 4)
    if format_type == 1:
        # ISO 8601
        time_str = format_iso_time(future_time)
    elif format_type == 2:
        # RFC 2822
        time_str = format_rfc_time(future_time)
    elif format_type == 3:
        # Unix timestamp
        time_str = str(int(future_time.timestamp()))
    else:
        # Duration format
        time_str = f"Now+PT{minutes}M"

    return future_time, time_str

def generate_level_6() -> Tuple[datetime, str]:
    """Generate time for level 6: Summation of time and duration"""
    now = get_current_time()
    minutes = random.randint(1, 60)
    seconds = random.randint(0, 59)
    base_time = add_time_delta(now, minutes=minutes - 1)  # Subtract 1 minute to add it in the expression
    future_time = add_time_delta(base_time, minutes=1, seconds=seconds)

    format_type = random.randint(1, 3)
    if format_type == 1:
        # ISO 8601
        time_str = f"{base_time.strftime('%Y-%m-%dT%H:%M:%S%z')[:-2]}:{base_time.strftime('%z')[-2:]} + PT{60+seconds}S"
    elif format_type == 2:
        # RFC 2822
        time_str = f"{base_time.strftime('%a, %d %b %Y %H:%M:%S %z')[:-2]}:{base_time.strftime('%z')[-2:]} + PT{60+seconds}S"
    else:
        # Unix timestamp
        time_str = f"{int(base_time.timestamp())} + PT{60+seconds}S"

    return future_time, time_str

def generate_level_7() -> Tuple[datetime, str]:
    """Generate time for level 7: Complex expression with summation and subtraction"""
    now = get_current_time()
    minutes = random.randint(2, 60)
    base_time = add_time_delta(now, minutes=minutes - 1)
    future_time = add_time_delta(base_time, minutes=1, seconds=5)
    future_time = add_time_delta(future_time, seconds=-5)  # Subtract 5 seconds

    time_str = f"{base_time.strftime('%Y-%m-%dT%H:%M:%S%z')[:-2]}:{base_time.strftime('%z')[-2:]} + PT1M5S - PT5S"

    return future_time, time_str

def generate_level_8() -> Tuple[datetime, str]:
    """Generate time for level 8: Natural language"""
    now = get_current_time()

    # Choose a pattern type (1-6)
    pattern_type = random.randint(1, 6)

    if pattern_type == 1:
        # "{minutes} minutes from now"
        minutes = random.randint(1, 60)
        future_time = add_time_delta(now, minutes=minutes)
        time_str = f"{minutes} minutes from now"
    elif pattern_type == 2:
        # "{hours} hours and {minutes} minutes from now"
        hours = random.randint(0, 1)
        minutes = random.randint(1, 59)
        future_time = add_time_delta(now, hours=hours, minutes=minutes)
        time_str = f"{hours} hours and {minutes} minutes from now"
    elif pattern_type == 3:
        # "Half past {hour}"
        current_hour = now.hour
        target_hour = (current_hour + 1) % 24  # Next hour
        future_time = now.replace(hour=target_hour, minute=30, second=0, microsecond=0)
        if future_time <= now:
            future_time += timedelta(days=1)
        time_str = f"Half past {target_hour}"
    elif pattern_type == 4:
        # "Quarter past {hour}"
        current_hour = now.hour
        target_hour = (current_hour + 1) % 24  # Next hour
        future_time = now.replace(hour=target_hour, minute=15, second=0, microsecond=0)
        if future_time <= now:
            future_time += timedelta(days=1)
        time_str = f"Quarter past {target_hour}"
    elif pattern_type == 5:
        # "Quarter to {hour}"
        current_hour = now.hour
        target_hour = (current_hour + 1) % 24  # Next hour
        next_hour = (target_hour + 1) % 24
        future_time = now.replace(hour=target_hour, minute=45, second=0, microsecond=0)
        if future_time <= now:
            future_time += timedelta(days=1)
        time_str = f"Quarter to {next_hour}"
    else:  # pattern_type == 6
        # "{hour} o'clock"
        current_hour = now.hour
        target_hour = (current_hour + 1) % 24  # Next hour
        future_time = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        if future_time <= now:
            future_time += timedelta(days=1)
        time_str = f"{target_hour} o'clock"

    return future_time, time_str

def generate_time_for_level(level: int) -> Tuple[datetime, str]:
    """Generate a time in the future based on the difficulty level"""
    # Call the appropriate level-specific function based on the level
    if level == 1:
        return generate_level_1()
    elif level == 2:
        return generate_level_2()
    elif level == 3:
        return generate_level_3()
    elif level == 4:
        return generate_level_4()
    elif level == 5:
        return generate_level_5()
    elif level == 6:
        return generate_level_6()
    elif level == 7:
        return generate_level_7()
    else:  # level == 8 or any other value
        return generate_level_8()

def parse_time_expression(time_expr: str) -> datetime:
    """Parse various time expressions to get a datetime object"""
    now = get_current_time()

    # ISO 8601 format: 2025-07-02T15:04:05+02:00
    iso_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}'

    # RFC 2822 format: Tue, 02 Jul 2025 15:04:05 +0200
    rfc_pattern = r'[A-Za-z]{3}, \d{2} [A-Za-z]{3} \d{4} \d{2}:\d{2}:\d{2} [+-]\d{4}'

    # Unix timestamp: 1720220645
    unix_pattern = r'^\d{10}$'

    # Duration format: Now+PT5S, Now+0:01:00
    duration_pattern = r'Now\+PT\d+[HMS]'
    alt_duration_pattern = r'Now\+\d+:\d{2}:\d{2}'

    # Expression with summation and subtraction
    expr_pattern = r'.*[+-].*'

    # Check for timezone abbreviations
    for tz_name in TIMEZONES:
        if tz_name in time_expr:
            # Replace timezone abbreviation with its offset
            tz = ZoneInfo(TIMEZONES[tz_name])
            time_expr = time_expr.replace(tz_name, '')
            dt = cast(datetime, parser.parse(time_expr))
            return dt.replace(tzinfo=tz)

    # Try parsing as ISO 8601
    if re.search(iso_pattern, time_expr):
        return cast(datetime, parser.parse(time_expr))

    # Try parsing as RFC 2822
    elif re.search(rfc_pattern, time_expr):
        return cast(datetime, parser.parse(time_expr))

    # Try parsing as Unix timestamp
    elif re.search(unix_pattern, time_expr):
        return datetime.fromtimestamp(int(time_expr), timezone.utc)

    # Try parsing as duration
    elif re.search(duration_pattern, time_expr):
        match = re.search(r'PT(\d+)([HMS])', time_expr)
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            if unit == 'H':
                return now + timedelta(hours=value)
            elif unit == 'M':
                return now + timedelta(minutes=value)
            else:  # unit == 'S'
                return now + timedelta(seconds=value)

    # Try parsing as alternative duration format
    elif re.search(alt_duration_pattern, time_expr):
        match = re.search(r'Now\+(\d+):(\d{2}):(\d{2})', time_expr)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            return now + timedelta(hours=hours, minutes=minutes, seconds=seconds)

    # Try parsing as expression with summation and subtraction
    elif re.search(expr_pattern, time_expr):
        # Split by + and -
        parts = re.split(r'([+-])', time_expr)
        result_time = None

        i = 0
        while i < len(parts):
            part = parts[i].strip()

            # Skip empty parts
            if not part:
                i += 1
                continue

            # If this is the first part or an operator
            if result_time is None or part in ['+', '-']:
                if part in ['+', '-']:
                    operator = part
                    i += 1
                    part = parts[i].strip()
                else:
                    operator = '+'

                # Parse the time part
                if part.startswith('PT'):
                    # Parse duration
                    match = re.search(r'PT(\d+)([HMS])', part)
                    if match:
                        value = int(match.group(1))
                        unit = match.group(2)
                        delta = None
                        if unit == 'H':
                            delta = timedelta(hours=value)
                        elif unit == 'M':
                            delta = timedelta(minutes=value)
                        else:  # unit == 'S'
                            delta = timedelta(seconds=value)

                        if result_time is None:
                            result_time = now

                        if operator == '+':
                            result_time += delta
                        else:
                            result_time -= delta
                elif part.lower() == 'now':
                    if result_time is None:
                        result_time = now
                else:
                    # Try to parse as a datetime
                    try:
                        time_part = parse_time_expression(part)
                        if result_time is None:
                            result_time = time_part
                        elif operator == '+':
                            # When adding two datetimes, we need to convert the second one to a timedelta
                            delta = time_part - now
                            result_time += delta
                        else:
                            delta = time_part - now
                            result_time -= delta
                    except:
                        # If we can't parse it, just ignore it
                        pass

            i += 1

        return result_time if result_time else now

    # Try parsing natural language
    else:
        # Check for specific patterns
        if "minutes from now" in time_expr:
            match = re.search(r'(\d+) minutes from now', time_expr)
            if match:
                minutes = int(match.group(1))
                return now + timedelta(minutes=minutes)

        elif "hours and" in time_expr and "minutes from now" in time_expr:
            match = re.search(r'(\d+) hours and (\d+) minutes from now', time_expr)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                return now + timedelta(hours=hours, minutes=minutes)

        elif "Half past" in time_expr:
            match = re.search(r'Half past (\d+)', time_expr)
            if match:
                hour = int(match.group(1))
                target_time = now.replace(hour=hour, minute=30, second=0, microsecond=0)
                if target_time <= now:
                    target_time += timedelta(days=1)
                return target_time

        elif "Quarter past" in time_expr:
            match = re.search(r'Quarter past (\d+)', time_expr)
            if match:
                hour = int(match.group(1))
                target_time = now.replace(hour=hour, minute=15, second=0, microsecond=0)
                if target_time <= now:
                    target_time += timedelta(days=1)
                return target_time

        elif "Quarter to" in time_expr:
            match = re.search(r'Quarter to (\d+)', time_expr)
            if match:
                hour = int(match.group(1))
                target_time = now.replace(hour=(hour-1)%24, minute=45, second=0, microsecond=0)
                if target_time <= now:
                    target_time += timedelta(days=1)
                return target_time

        elif "o'clock" in time_expr:
            match = re.search(r'(\d+) o\'clock', time_expr)
            if match:
                hour = int(match.group(1))
                target_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                if target_time <= now:
                    target_time += timedelta(days=1)
                return target_time

    # Default: return current time
    return now

@router.get("/statements", response_model=Dict[str, str])
async def get_statements() -> Dict[str, str]:
    """Get the task statements"""
    return STATEMENTS

@router.post("/gen", response_model=GenResponse)
async def generate_task(request: GenRequest) -> GenResponse:
    """Generate a new right_time task"""
    # Determine the difficulty level
    level = get_difficulty_level(request)

    # Generate a time based on the difficulty level
    future_time, time_str = generate_time_for_level(level)

    # Create the input string (the time expression)
    input_data = time_str

    # Store the expected submission time as a hint for the checker
    checker_hint = future_time.isoformat()

    statement_key = f"v{level}"
    return GenResponse(
        statement_version=statement_key,
        statement=STATEMENTS[statement_key],
        score=100,
        input=input_data,
        checker_hint=checker_hint
    )

@router.post("/check", response_model=CheckResult)
async def check_answer(request: CheckRequest) -> CheckResult:
    """Check the answer for a right_time task"""
    try:
        # Get the target time from the checker hint
        target_time = parser.parse(request.checker_hint.strip())

        # Get the current time
        now = datetime.now(timezone.utc)

        # Calculate the time difference in seconds
        time_diff = abs((now - target_time).total_seconds())

        # Check if the submission is within the allowed time window (±2 seconds)
        if time_diff <= 2:
            return CheckResult(status=CheckStatus.ACCEPTED, score=1.0)
        else:
            return CheckResult(
                status=CheckStatus.WRONG_ANSWER,
                score=0.0,
                error=f"Expected submission at {target_time.isoformat()}, but received at {now.isoformat()}. Time difference: {time_diff:.2f} seconds."
            )
    except Exception as e:
        return CheckResult(
            status=CheckStatus.WRONG_ANSWER,
            score=0.0,
            error=f"Error processing answer: {str(e)}"
        )
