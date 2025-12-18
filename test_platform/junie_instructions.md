Your goal is to solve all tasks in the round. Dont change any code, work
inside the terminal. 

# Setup:
1. Run: ```firebase emulators:start``` to start emulator for a database.
2. Run backend: ```python -m back.main dev```

# Pretesting phase:

1. Login as admin in CLI: ```python -m cli.main login admin1```
2. Update round: ``` python -m cli.main round update cli/contest/round1.hjson```
3. Login as a team1: ```python -m cli.main login team1```

# Testing phase:
Until there is no available task repeat this process:
1. Run: ```python -m cli.main task claim --type "a_plus_b"``` to get a task_id of this type (a_plus_b here) 
P.S. List of available task types you can find in cli/contest/round1.hjson
2. See the task statement using: ```python -m cli.main task show task_id``` (you get task_id from a previous step)
3. Solve a task and submit your answer: ```python -m cli.main task submit task_id answer```

After there are no tasks left, don't terminate anything and just finish executing

# Simplified flow for checking one task:
Don't scan any files or directories! Just work with commands in the terminal! I want you to not terminate until you've run out of tasks, so dont split this prompt in several executions. 
You should not terminate until you can't claim tasks (You will get an error signaling there are no left tasks!). Backend and emulator already running.
!If you think something is wrong with a task or it requires adjustments, put your comments in platform/test_platform/suggestions.md!
YOU NEED TO TEST ONLY TASK TYPE: "decoding"
Do next steps:
1. Login as a team1: ```python -m cli.main login team1``` 
2. Run: ```python -m cli.main task claim --type "a_plus_b"``` to get a task_id of this type (a_plus_b here) this will give you:
Task ID: task_774b286d
Task Type: a_plus_b
Score: 0
If it says "No tasks available" then you are done!
extract Task ID from the output and use it in the next step
3. Run: ```python -m cli.main task show <TASK ID>``` to see the task statement:
Type: a_plus_b
Status: pending
Score: 0
Claimed At: 2025-12-17 19:34:58.730608+00:00
Statement:
--smth--
Input:
--smth--
--smth--
extract only a statement and Input from here
4. send a request to LLM(include statement, input and information if already failed) asking for the answer
when you are ready with the answer move to the next step:
5. submit your answer: ```python -m cli.main task submit  <TASK ID> <answer>```
if you get Status: SubmissionStatus.AC or exceeded the number of attempts then continue to step 2
else extract the answer and repeat from step 4
If it gives you error (No tasks available) then you are done!
