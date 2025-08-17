from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import requests
import json
from api_models import GenRequest, GenResponse, TaskProgress, CheckRequest, CheckResult, CheckStatus, CheckResponse
from api_models import Submission as ApiSubmission, SubmissionStatus, TaskStatus as ApiTaskStatus
from back.db_models import Team, Task, Round, RoundTaskType, Submission
import random
import logging
from pydantic import TypeAdapter

class TaskGenClient:
    """Client for interacting with task generator service."""
    
    def generate_task(self, generator_url: str, generator_secret: str, gen_request: GenRequest) -> GenResponse:
        """Generate task content by calling the task generator and return the generator response."""
        try:
            response = requests.post(
                f"{generator_url}/gen",
                headers={"Content-Type": "application/json", "X-API-KEY": generator_secret or ""},
                data=json.dumps(gen_request.model_dump())
            )

            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 401 or response.status_code == 403:
                    raise RuntimeError(f"Authentication error with task generator: {http_err}")
                elif response.status_code == 404:
                    raise RuntimeError(f"Task generator endpoint not found: {generator_url}/gen")
                elif response.status_code >= 500:
                    raise RuntimeError(f"Task generator server error: {http_err}")
                else:
                    raise RuntimeError(f"HTTP error when calling task generator: {http_err}")

            try:
                gen_response = GenResponse.model_validate(response.json())
            except json.JSONDecodeError:
                raise RuntimeError("Invalid JSON response from task generator")
            except Exception as validation_err:
                raise RuntimeError(f"Invalid response format from task generator: {validation_err}")

            return gen_response

        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"Could not connect to task generator at {generator_url}")
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Connection to task generator timed out")
        except requests.exceptions.RequestException as req_err:
            raise RuntimeError(f"Error making request to task generator: {req_err}")
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"Unexpected error generating task: {str(e)}")

    def check_answer(self, generator_url: str, answer: str, checker_hint: str, input_text: str, task_id: str | None = None) -> CheckResponse:
        check_request = CheckRequest(
            input=input_text,
            answer=answer,
            checker_hint=checker_hint,
            task_id=task_id
        )

        try:
            response = requests.post(
                f"{generator_url}/check",
                headers={"Content-Type": "application/json"},
                data=json.dumps(check_request.model_dump())
            )
            response.raise_for_status()

            adapter = TypeAdapter(list[CheckResult])
            parsed = adapter.validate_python(response.json())
            check_response = CheckResponse(parsed)

            if len(check_response) == 0:
                raise RuntimeError("No check results returned from task generator")

            return check_response

        except Exception as e:
            raise RuntimeError(f"Error checking answer: {str(e)}")
