## General issues
502 server error when exceeded number of tasks. FIXED!
---
It might be better printing expected answers/inputs in normal human format not as arrays(Matrices in a_plus_b, hints in interpreter)
also formate whole output in general(like printing expected output from new line so it looks nice)
currently: 
Message: Expected [79
wahr
3763
6864], got [1322]
---

## a_plus_b
# Negative numbers considered as CLI params
python -m cli.main task submit task_ced73f7d -350775154342610666813428812442
Fix:
python -m cli.main task submit task_ced73f7d -- -350775154342610666813428812442
---
# in matrix addition, check how the answer can be provided (Junie could submit only with a file path or $')
---
# check if for complex numbers answer can be submitted in format 1+2j, 2j+1... (Junie submitted only in format (78+83j))

## decoding

# LLM couldn't solve tasks with Affine Cipher without formula, decoding method hinted in previous level(swap and reverse) and combined Morse + Affine Cipher. 
 
TODO: 
keep formula in Affine Cipher but in general form
delete level with hints in Morse
change to two lines where first one is hint, second - sentence 


---
# add hints in messages?? 
---
# get rid of last level with encoding (Huffman)

## interpreter
Output includes evaluation of all lines(instead of just print lines) FIXED!
---
For True/False logical statements output is unclear and Expected message didn't appear. FIXED!
---
Empty Statement. FIXED!
---

TODO: add oder to sample level 9
add to decoding code from interpreter
add to interpreter numbers in format from a_plus_b
add to decoding expressions from a_plus_b

TODO:
take task type -> generatr all tasks and show input, hint answer ... -> report in file. FIXED!

CHECK ALL WAYS OF SUBMISSION (CLI, JSON, file for all tasks)


## tricky_maze
LLM can't solve this task, tried infinite amount of prompts, none of them worked!

show-answer in CLI doesnt work. FIXED!

## right_time
INFO from CLI:
Task ID: task_58c8e70d
Status: wa
Score: 0
Submitted At: 2026-01-09 00:52:17.954767+00:00
Checker Output: Expected submission at 2026-01-09T00:52:16.341036+00:00, but received at 
2026-01-09T00:52:19.987816+00:00. Time difference: 3.65 seconds.


INFO from LLM:
- **2026-01-09 task_58c8e70d**: Input "2026-01-09T00:51:16+00:00 + PT1M5S - PT5S"
  - **My Calculation**:
    - Base time: 2026-01-09T00:51:16+00:00
    - Add: PT1M5S = 1 minute 5 seconds = 65 seconds
    - Subtract: PT5S = 5 seconds
    - Result: 00:51:16 + 65s - 5s = 00:51:16 + 60s = **2026-01-09T00:52:16+00:00**
  - **Checker Expected**: "2026-01-09T00:52:16.341036+00:00"
  - **My Submission Time**: 2026-01-09T00:52:17.340196+00:00
  - **Time Difference**: +1.34 seconds (submitted 1.34s after target)
  - **Tolerance Claimed**: ±3 seconds

checked task 8 using report file, all checker_hints are correct!

TODO: level 7 fix hard code