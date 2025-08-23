import random
import io
import sys
from statistics import variance

# ========= Random helpers =========
POOL = ["a", "b", "c", "e", "f", "g", "h",
        "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
LOOP_POOL = ["i", "j", "k", "l", "m", "d", 'p', 'q']
LOOP_VARIABLES = []
VARIABLES = []


def rnum(lo=0, hi=10):
    return str(random.randint(lo, hi))


def arith_op():
    # prefer + and * for variety; include -, %, and / (safe-div ensured)
    return random.choices(["+", "-", "*", "%", "/"], weights=[3, 2, 3, 1, 1])[0]


def cmp_op():
    return random.choice(["<", "<=", ">", ">=", "==", "!="])


def logic_op():
    return random.choice(["und", "oder"])


def maybe_not(expr):
    return expr if random.random() < 0.5 else f"nicht {expr}"


def brace(expr):
    # Your grammar treats { ... } as parentheses
    return "{" + expr + "}"


def rand_term():
    """Either a number or a variable (usually initialized by each generator)."""
    if random.random() < 0.5 or not VARIABLES:
        return rnum(0, 100)
    return random.choice(VARIABLES)


def rand_arith(depth=0, max_depth=2):
    """Build a random arithmetic expression that your grammar accepts."""
    if depth >= max_depth or random.random() < 0.35:
        # base: unary or atom
        if random.random() < 0.2:
            return rand_arith(depth + 1, max_depth)
        return rand_term()

    # binary
    op = arith_op()
    left = rand_arith(depth + 1, max_depth)
    if op == "/" or op == "%":
        right = rnum(1, 9)
    else:
        right = rand_arith(depth + 1, max_depth)

    # occasionally wrap with braces for grouping
    if op != '-' and random.random() < 0.1:
        expr = f"{left} {op} {brace('-' + right)}"
    else:
        expr = f"{left} {op} {right}"
    return expr if random.random() < 0.6 else brace(expr)


def rassign():
    variable = random.choice(POOL)
    answer = f"{variable} = {rand_arith(max_depth=random.randint(1, 3))}"
    VARIABLES.append(variable)
    return answer


def rand_cmp():
    return f"{brace(rand_arith())} {cmp_op()} {brace(rand_arith())}"


def rand_bool(depth=0, max_depth=3):
    """Boolean/logic expression: comparisons + und/oder + optional nicht."""
    # Base: a comparison
    node = rand_cmp()
    # Optionally chain with logic ops
    while depth < max_depth and random.random() < 0.5:
        node = f"{node} {logic_op()} {rand_cmp()}"
        depth += 1
        if random.random() < 0.3:
            node = brace(node)
    # Optional leading 'nicht'
    if random.random() < 0.4:
        node = f"nicht {brace(node)}"
    return node


def generate_script(length=5, allow_cmp=False, allow_bool=False):
    code = []
    for _ in range(length - 1):
        choice = random.random()
        if choice < 0.6:  # mostly assignments
            code.append(rassign())
        elif choice < 0.8:  # arithmetic expression print
            code.append(f"ausgeben{{{rand_arith(max_depth=random.randint(1, 3))}}}")
        else:  # comparisons / booleans if allowed
            if allow_bool:
                code.append(f"ausgeben{{{rand_bool()}}}")
            elif allow_cmp:
                code.append(f"ausgeben{{{rand_cmp()}}}")
            else:
                code.append(f"ausgeben{{{rand_arith(max_depth=random.randint(1, 3))}}}")

    # last line always a print (arith / cmp / bool)
    if allow_bool:
        printer = rand_bool() if random.random() < 0.5 else rand_arith(max_depth=random.randint(1, 3))
    elif allow_cmp:
        printer = rand_cmp() if random.random() < 0.5 else rand_arith(max_depth=random.randint(1, 3))
    else:
        printer = rand_arith(max_depth=random.randint(1, 3))
    code.append(f"ausgeben{{{printer}}}")
    return code


def generate_if_else(depth=2, max_code_len=3):
    """
    Generate a nested if/else block.
    depth: remaining nesting depth
    max_code_len: number of statements in each block
    """
    global VARIABLES
    code = []

    if random.random() < 0.5:
        code.extend(generate_script(random.randint(1, 3), allow_cmp=True, allow_bool=True))

    code.append(f"wenn {rand_bool()}")
    variables_holder = VARIABLES.copy()
    num_statements = random.randint(1, max_code_len)
    for _ in range(num_statements):
        choice = random.random()
        if depth > 1 and choice < 0.4:
            # nested if
            code.extend(["    " + line for line in generate_if_else(depth - 1, max_code_len)])
        else:
            # normal code
            code.extend(
                ["    " + line for line in generate_script(random.randint(1, 3), allow_cmp=True, allow_bool=True)])
    VARIABLES = variables_holder.copy()

    # --- optional else ---
    if random.random() < 0.5:
        code.append("sonst")
        variables_holder = VARIABLES.copy()
        num_statements = random.randint(1, max_code_len)
        for _ in range(num_statements):
            choice = random.random()
            if depth > 1 and choice < 0.5:
                code.extend(["    " + line for line in generate_if_else(depth - 1, max_code_len)])
            else:
                code.extend(
                    ["    " + line for line in generate_script(random.randint(1, 3), allow_cmp=True, allow_bool=True)])
        VARIABLES = variables_holder.copy()
    code.append("ende")

    if random.random() < 0.5:
        code.extend(generate_script(random.randint(1, 3), allow_cmp=True, allow_bool=True))

    return code


def generate_while_safe(depth=1, max_code_len=4):
    """
    Generate a solange (while) loop that depends on a single variable,
    and modifies it inside (increment/decrement) to prevent infinite loops.
    """
    global LOOP_VARIABLES, VARIABLES
    code = []

    # Pick a variable (use an existing one or create new if none given)
    if len(LOOP_POOL) == len(LOOP_VARIABLES):
        return ["///hm... some random comments here"]
    var = random.choice(LOOP_POOL)
    while var in LOOP_VARIABLES:
        var = random.choice(LOOP_POOL)
    LOOP_VARIABLES.append(var)
    bool_op_pool = random.choice(["<", ">", "<=", ">="])
    value = random.randint(1, 10)
    cmp_val = random.randint(1, 10)
    if bool_op_pool == "<" or bool_op_pool == "<=":
        if value > cmp_val:
            value, cmp_val = cmp_val, value
    else:
        if value < cmp_val:
            value, cmp_val = cmp_val, value
    code.append(f"{var} = {value}")  # initialize if new

    code.append(f"solange {{{var} {bool_op_pool} {cmp_val}}}")
    if value < cmp_val:
        code.append(f"    {var}++")
    else:
        code.append(f"    {var}--")
    # Loop body
    variables_holder = VARIABLES.copy()
    num_statements = random.randint(1, max_code_len)
    for _ in range(num_statements):
        choice = random.random()
        if depth > 1 and choice < 0.4:
            code.extend(["    " + line for line in generate_while_safe(depth - 1, max_code_len)])
        else:
            # normal code
            code.extend(
                ["    " + line for line in generate_script(random.randint(1, 3), allow_cmp=True, allow_bool=True)])

    VARIABLES = variables_holder.copy()
    LOOP_VARIABLES.remove(var)
    code.append("ende")

    return code


def gen_level_1():
    return generate_script(random.randint(1, 10), allow_cmp=False, allow_bool=False)


def gen_level_2():
    return generate_script(random.randint(1, 10), allow_cmp=True, allow_bool=False)


def gen_level_3():
    return generate_script(random.randint(1, 10), allow_cmp=True, allow_bool=True)


def gen_level_4():
    """
    Generate a code block with:
    - assignments
    - arithmetic prints
    - nested if/else blocks
    """
    code = []
    # nested if
    code.extend(generate_if_else(depth=random.randint(1, 2), max_code_len=random.randint(1, 2)))

    # always end with a print
    code.append(f"ausgeben{{{rand_arith(max_depth=random.randint(1, 3))}}}")
    return code


def gen_level_5():
    """
    Generate code with safe solange loops.
    Condition depends on one variable, and loop body ensures variable changes.
    """
    code = generate_while_safe(depth=random.randint(1, 2), max_code_len=random.randint(1, 6))
    return code

def gen_level_6():
    """
    Generate code with mixed:
    - if/else blocks
    - safe solange loops
    Allows nesting of both types.
    """
    code = []
    num_blocks = random.randint(2, 6)  # total number of top-level statements/blocks

    for _ in range(num_blocks):
        choice = random.random()
        if choice < 0.4:
            # Generate an if/else block
            code.extend(generate_if_else(depth=random.randint(1, 2), max_code_len=random.randint(1, 3)))
        elif choice < 0.8:
            # Generate a safe solange loop
            code.extend(generate_while_safe(depth=random.randint(1, 2), max_code_len=random.randint(1, 4)))
        else:
            # Generate normal script statements
            code.extend(generate_script(random.randint(1, 3), allow_cmp=True, allow_bool=True))

    return code

def gen_level_7(depth=2, max_code_len=3):
    """
    Generate mixed code with nested if/else and safe solange loops.
    depth: max nesting depth
    max_code_len: number of statements in each block
    """
    code = []
    num_blocks = random.randint(1, max_code_len)

    for _ in range(num_blocks):
        choice = random.random()
        if depth > 0:
            if choice < 0.35:
                inner_code = generate_if_else(depth=random.randint(1, depth), max_code_len=max_code_len)
                if random.random() < 0.5:
                    for i in range(len(inner_code)):
                        if "ende" in inner_code[i]:
                            inner_code[i:i] = ["    " + line for line in generate_while_safe(depth=random.randint(1, depth), max_code_len=max_code_len)]
                            break
                code.extend(inner_code)
            elif choice < 0.7:
                inner_code = generate_while_safe(depth=random.randint(1, depth), max_code_len=max_code_len)
                for i in range(len(inner_code)):
                    if inner_code[i].startswith("    "):
                        if random.random() < 0.5:
                            inner_code[i:i] = ["    " + line for line in generate_if_else(depth=random.randint(1, depth-1), max_code_len=max_code_len)]
                            break
                code.extend(inner_code)
            else:
                # Normal statements
                code.extend(generate_script(random.randint(1, 3), allow_cmp=True, allow_bool=True))
        else:
            # Depth limit reached, only normal statements
            code.extend(generate_script(random.randint(1, 3), allow_cmp=True, allow_bool=True))

    return code

def gen_level_8():
    code = gen_level_7()
    new_code = []
    for line in code:
        # Randomly insert empty lines
        if random.random() < 0.2:
            new_code.append("")


        if random.random() < 0.2:
            comment = f"/// {''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=random.randint(5, 15)))}"
            new_code.append(comment)

        # Randomly add leading/trailing spaces
        spaces_before = " " * random.randint(0, 4)
        spaces_after = " " * random.randint(0, 4)
        formatted_line = f"{spaces_before}{line}{spaces_after}"
        if random.random() < 0.2:
            comment = f"/// {''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=random.randint(5, 15)))}"
            formatted_line += comment

        new_code.append(formatted_line)

        # Randomly add comment lines
        if random.random() < 0.15:
            comment = f"/// {''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=random.randint(5,15)))}"
            new_code.append(comment)

    # Possibly add some empty lines at the end
    for _ in range(random.randint(0, 2)):
        new_code.append("")

    return new_code

print('\n'.join(gen_level_8()))
