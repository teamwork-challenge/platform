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
  Suggestion: Investigate a_plus_b task generator service on port 8089; ensure it is running and returns valid JSON. Add resilience/error mapping in back/services/taskgen_client.py to surface clearer user-facing message when generator fails.
