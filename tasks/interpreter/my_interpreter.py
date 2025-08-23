import re
import sys


# --- Tokenizer ---
def tokenize(code_line):
    code_line = code_line.split("///")[0]
    token_spec = [
        ("NUMBER", r"\d+"),
        ("LPAREN", r"\{"),
        ("RPAREN", r"\}"),
        ("INCR", r"\+\+"),
        ("DECR", r"--"),
        ("EQ", r"=="),
        ("NE", r"!="),
        ("LE", r"<="),
        ("GE", r">="),
        ("OP", r"[+\-*/=<>%]"),
        ("VARIABLE", r"[a-zA-Z_]\w*"),
        ("SKIP", r"[ \t]+"),
    ]
    token_re = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in token_spec))

    tokens_pull = []
    for m in token_re.finditer(code_line):
        kind = m.lastgroup
        value = m.group()
        if kind == "SKIP":
            continue
        if kind == "NUMBER":
            value = int(value)
        tokens_pull.append((kind, value))
    return tokens_pull


# --- Parser ---
class Parser:
    def __init__(self, lines_tokens):
        self.lines = lines_tokens
        self.line_pos = 0
        self.tokens = []
        self.pos = 0
        self.next_line()

    def next_line(self):
        if self.line_pos < len(self.lines):
            self.tokens = self.lines[self.line_pos]
            self.pos = 0
            self.line_pos += 1
            return True
        return False

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else (None, None)

    def eat(self, kind=None):
        tok = self.peek()
        if kind and tok[0] != kind:
            raise SyntaxError(f"Expected {kind}, got {tok}")
        self.pos += 1
        return tok

    def parse_statement(self):
        tok = self.peek()
        if tok[0] == "VARIABLE":
            # print
            if tok[1] == "ausgeben":
                self.eat("VARIABLE")
                expr = self.parse_logic()
                return "print", expr

            # while loop
            if tok[1] == "solange":
                self.eat("VARIABLE")
                condition = self.parse_logic()
                body = []
                while True:
                    if not self.next_line():
                        raise SyntaxError("Fehlendes 'ende' für solange Schleife")
                    if self.peek()[0] == "VARIABLE" and self.peek()[1] == "ende":
                        self.eat("VARIABLE")
                        break
                    stmt = self.parse_statement()
                    body.append(stmt)
                return "while", condition, body

            # if statement
            if tok[1] == "wenn":
                self.eat("VARIABLE")
                condition = self.parse_logic()
                if_body = []
                else_body = []

                while True:
                    if not self.next_line():
                        raise SyntaxError("Fehlendes 'ende' für wenn Anweisung")
                    next_tok = self.peek()
                    if next_tok[0] == "VARIABLE" and next_tok[1] == "sonst":
                        self.eat("VARIABLE")
                        while True:
                            if not self.next_line():
                                raise SyntaxError("Fehlendes 'ende' für wenn Anweisung")
                            if self.peek()[0] == "VARIABLE" and self.peek()[1] == "ende":
                                self.eat("VARIABLE")
                                break
                            stmt = self.parse_statement()
                            else_body.append(stmt)
                        break
                    elif next_tok[0] == "VARIABLE" and next_tok[1] == "ende":
                        self.eat("VARIABLE")
                        break
                    else:
                        stmt = self.parse_statement()
                        if_body.append(stmt)
                return "if", condition, if_body, else_body

            # --- Assignment handling ---
            name = tok[1]
            if (self.pos + 1 < len(self.tokens)) and self.tokens[self.pos + 1][1] == "=":
                self.eat("VARIABLE")
                self.eat("OP")  # '='
                expr = self.parse_logic()
                return "assign", name, expr

        # --- Fallback to expression ---
        return self.parse_logic()

    # --- Logical expressions with correct precedence ---
    def parse_logic(self):
        return self.parse_or()

    def parse_or(self):
        node = self.parse_and()
        while True:
            tok = self.peek()
            if tok[0] == "VARIABLE" and tok[1] == "oder":
                self.eat("VARIABLE")
                right = self.parse_and()
                node = ("logic", "oder", node, right)
            else:
                break
        return node

    def parse_and(self):
        node = self.parse_not()
        while True:
            tok = self.peek()
            if tok[0] == "VARIABLE" and tok[1] == "und":
                self.eat("VARIABLE")
                right = self.parse_not()
                node = ("logic", "und", node, right)
            else:
                break
        return node

    def parse_not(self):
        tok = self.peek()
        if tok[0] == "VARIABLE" and tok[1] == "nicht":
            self.eat("VARIABLE")
            expr = self.parse_not()
            return "not", expr
        return self.parse_comparison()

    # --- Comparison / arithmetic ---
    def parse_comparison(self):
        tok = self.peek()
        if tok[0] == "VARIABLE" and tok[1] == "nicht":
            self.eat("VARIABLE")
            expr = self.parse_comparison()
            return "not", expr
        node = self.parse_expr()
        tok = self.peek()
        if tok[0] in ("OP", "EQ", "NE", "LE", "GE") and tok[1] in ("<", "<=", ">", ">=", "==", "!="):
            op = self.eat()[1]
            right = self.parse_expr()
            node = ("compare", op, node, right)
        return node

    def parse_expr(self):
        node = self.parse_term()
        while self.peek()[1] in ("+", "-"):
            op = self.eat("OP")[1]
            right = self.parse_term()
            node = ("binop", op, node, right)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek()[1] in ("*", "/", "%"):
            op = self.eat("OP")[1]
            right = self.parse_factor()
            node = ("binop", op, node, right)
        return node

    def parse_factor(self):
        tok = self.peek()
        if tok[0] == "OP" and tok[1] == "-":
            self.eat("OP")
            factor = self.parse_factor()
            return "unary", "-", factor
        elif tok[0] == "NUMBER":
            self.eat("NUMBER")
            return "num", tok[1]
        elif tok[0] == "VARIABLE":
            self.eat("VARIABLE")
            node = ("var", tok[1])
            next_tok = self.peek()
            if next_tok[0] == "INCR":
                self.eat("INCR")
                return "postinc", tok[1]
            elif next_tok[0] == "DECR":
                self.eat("DECR")
                return "postdec", tok[1]
            return node
        elif tok[0] == "LPAREN":
            self.eat("LPAREN")
            expr = self.parse_logic()
            self.eat("RPAREN")
            return expr
        else:
            raise SyntaxError(f"Unexpected token {tok}")


# --- Evaluator ---
def eval_ast(node, table):
    kind = node[0]

    if kind == "num":
        return node[1]
    elif kind == "var":
        name = node[1]
        if name not in table:
            raise NameError(f"Variable {name} not defined")
        return table[name]
    elif kind == "assign":
        _, name, expr = node
        value = eval_ast(expr, table)
        table[name] = value
        return value
    elif kind == "binop":
        _, op, left, right = node
        lval, rval = eval_ast(left, table), eval_ast(right, table)
        if op == "+": return lval + rval
        if op == "-": return lval - rval
        if op == "*": return lval * rval
        if op == "/": return lval // rval
        if op == "%": return lval % rval
    elif kind == "unary":
        _, op, expr = node
        val = eval_ast(expr, table)
        if op == "-": return -val
    elif kind == "print":
        val = eval_ast(node[1], table)
        print(val)
        return val
    elif kind == "compare":
        _, op, left, right = node
        lval, rval = eval_ast(left, table), eval_ast(right, table)
        if op == "<": return lval < rval
        if op == "<=": return lval <= rval
        if op == ">": return lval > rval
        if op == ">=": return lval >= rval
        if op == "==": return lval == rval
        if op == "!=": return lval != rval
    elif kind == "logic":
        _, op, left, right = node
        lval, rval = eval_ast(left, table), eval_ast(right, table)
        if op == "und": return lval and rval
        if op == "oder": return lval or rval
    elif kind == "not":
        val = eval_ast(node[1], table)
        return not val
    elif kind == "while":
        _, condition, body = node
        last_val = None
        while eval_ast(condition, table):
            for stmt in body:
                last_val = eval_ast(stmt, table)
        return last_val
    elif kind == "if":
        _, condition, if_body, else_body = node
        if eval_ast(condition, table):
            last_val = None
            for stmt in if_body:
                last_val = eval_ast(stmt, table)
            return last_val
        else:
            last_val = None
            for stmt in else_body:
                last_val = eval_ast(stmt, table)
            return last_val
    elif kind == "postinc":
        name = node[1]
        if name not in table:
            raise NameError(f"Variable {name} not defined")
        table[name] += 1
        return table[name]
    elif kind == "postdec":
        name = node[1]
        if name not in table:
            raise NameError(f"Variable {name} not defined")
        table[name] -= 1
        return table[name]
    else:
        raise ValueError(f"Unknown node {node}")


# --- Executor ---
def executor(source_code, table=None):
    if table is None:
        table = {}

    tokenized_lines = []
    for line in source_code:
        line = line.strip()
        if not line or line.startswith("///"):
            continue
        tokenized_lines.append(tokenize(line))

    parser = Parser(tokenized_lines)
    while parser.line_pos <= len(tokenized_lines):
        if parser.pos >= len(parser.tokens):
            if not parser.next_line():
                break
        stmt = parser.parse_statement()
        eval_ast(stmt, table)

    return table


# --- Example usage ---
lines = [line.strip() for line in sys.stdin if line.strip()]
# lines = [line.rstrip('\n') for line in sys.stdin]

env = executor(lines)
print("Final Env:", env)
