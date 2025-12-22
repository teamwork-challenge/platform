- 2025-12-17 22:33: Task claim error for type a_plus_b: backend returned 500 from task generator
  Details:
  - Command: python -m cli.main task claim --type "a_plus_b"
  - Error chain shows back/services/taskgen_client.py raising RuntimeError due to 500 Server Error for url: http://localhost:8089/a_plus_b/gen
  - This blocks progress on claiming new a_plus_b tasks despite being logged in as team1.
  Steps to reproduce:
  1. Ensure backend and emulator are running (as per junie_instructions.md)
  2. python -m cli.main login team1
  3. python -m cli.main task claim --type "a_plus_b"
  Observed: HTTPError -> 500 from generator; call stack in FastAPI logs.
  Expected: Either a generated task is returned or a clear "No tasks available" / rate-limit message.
  Suggestion: Investigate task generator service on port 8089; ensure it is running and returns valid JSON. Add resilience/error mapping in back/services/taskgen_client.py to surface clearer user-facing message when generator fails.

- task_ba31650e: submission resulted in server error (500) from task checker expecting list[CheckResult] but got dict; my decoded answer was: "how beautiful she is".

- task_7e2ff9de: submission hit server error (500) from checker (expected list[CheckResult]). My decoded answer: "i got a smoothie while i was waiting for my plane to arrive".

- task_6b005e6f: submission hit server error (500) from checker (expected list[CheckResult]). My decoded answer: "the white water rafting trip was suddenly halted by the unexpected brick wall".

- task_ca9420b3: submission hit server error (500) from checker (expected list[CheckResult]). My decoded answer: "i want to ask them when their big day is".

- task_1f54b1c7: submission hit server error (500) from checker (expected list[CheckResult]). My decoded answer: "he got a fantastic performance review".

- task_37cbae96 (decoding): submission failed due to backend 500 at /decoding/check. My decoded answer was: "the sirens went off in the middle of the night and woke us all up". Likely infra issue, not logic.


- task_0cfd7d3c: Decoded Morse fine but misspelled the last word; should be "characters", not "charactear".

- task_8f007e65: Initial submission had spaces; expected contiguous lowercase string without spaces. Resubmitting without spaces.