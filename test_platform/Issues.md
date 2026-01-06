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
take task type -> generatr all tasks and show input, hint answer ... -> report in file 



