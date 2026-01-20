Your goal is to test a cli platform tasks. Here are some rules for you and flow of testing proccess through command line:
- You can find all the documentation about the platform in platform/docs folder if you need. 
- Just work with commands in the terminal! I want you to not terminate until you've run out of tasks, so dont split this prompt in several executions. 
- You should not terminate until you can't claim tasks (You will get an error signaling there are no left tasks!). 
- Backend and emulator already running.
- For each wrong submission write shortly your opinion about it and what was wrong in this file platform/test_platform/suggestions.md!
YOU NEED TO TEST ONLY THIS TASKS TYPES (If not specified test all tasks listed in platform/cli/contest/round1.hjson): "tricky_maze"
Do next steps:
1. Login as a team1: ```py -m cli.main login team1``` 
2. Run: ```py -m cli.main task claim --type "a_plus_b"``` to get a task_id of this type (a_plus_b here) this will give you:
Task ID: task_774b286d
Task Type: a_plus_b
Score: 0
If it says "No tasks available," then you are done!
extract Task ID from the output and use it in the next step
3. Run: ```py -m cli.main task show <TASK ID>``` to see the task statement:
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
4. using statement, input and information about failure, find the answer.
when you are ready with the answer, move to the next step:
5. submit your answer: ```py -m cli.main task submit  <TASK ID> <answer>```
if you get Status: SubmissionStatus.AC or exceeded the number of attempts then continue to step 2
else extract the answer and repeat from step 4
If it gives you error (No tasks available) then you are done!
6. DONT TERMINATE UNTIL YOU GET AN ERROR CLEARLY INDICATING THAT YOU CAN'T CLAIM ANY MORE TASKS!

After execution write the review about each task type. What tasks were hard to understand how to solve in your opinion. Write your suggestions how would you change a task. What is not user friendly in API in your opinion? 