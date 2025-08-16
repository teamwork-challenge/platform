# Custom Mini Language (German-style Syntax)

This is a simple educational programming language with German-style keywords and C-like arithmetic and control structures.  

---

## 1. Variables & Numbers
- Variables: [a-zA-Z_]\w*  
- Numbers: integers only (123, 0, etc.)  
- Assignment: =  

Example:
x = 5
y = x + 3

---

## 2. Arithmetic Operations

| Symbol | Meaning      |
|--------|--------------|
| +      | Addition     |
| -      | Subtraction  |
| *      | Multiplication |
| /      | Integer division |
| %      | Modulo       |
| ++     | Post-increment (x++) |
| --     | Post-decrement (x--) |
| -x     | Unary minus |

---

## 3. Comparison / Relational Operators

| Symbol | Meaning       |
|--------|---------------|
| <      | Less than     |
| <=     | Less or equal |
| >      | Greater than  |
| >=     | Greater or equal |
| ==     | Equal         |
| !=     | Not equal     |

---

## 4. Logical Operators

| Keyword | Meaning      |
|---------|-------------|
| nicht   | NOT         |
| und     | AND         |
| oder    | OR          |

Examples:
nicht x == 0
x < 5 und y > 3
x == 1 oder y != 0

---

## 5. Blocks / Control Flow (German Keywords)

| Keyword | English Meaning  | Usage / Notes |
|---------|----------------|---------------|
| solange | while         | Loop with a condition |
| wenn    | if            | Conditional statement |
| sonst   | else          | Optional else block |
| ende    | end           | Closes solange or wenn blocks |

Example:
solange x < 5
    ausgeben{x}
    x++
ende

---

## 6. Printing
| Keyword | English |
|---------|---------|
| ausgeben{} | print |

Example:
ausgeben{x + 2}

---

## 7. Grouping / Precedence
- Curly braces {} are used to group expressions instead of parentheses.

Examples:
ausgeben{ {x + 1} * 2 }
nicht { x < 3 und x == 2 }

---

## 8. Comments
- Single-line comments start with ///  

Example:
x = 5 /// this is a comment

---

## 9. Full Example Program
x = 0
y = 10

solange x < 5 und nicht y == 0
    ausgeben{x + y}   /// print current sum
    x++
    y--
ende

wenn x == 5
    ausgeben{x}
sonst
    ausgeben{y}
ende

---

## 10. Notes
- Supports ++ and -- as post-increment/decrement.
- Logical operators nicht, und, oder can be combined with {} for grouping.
- Comments and empty lines are ignored.
