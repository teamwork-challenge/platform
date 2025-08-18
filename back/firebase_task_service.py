from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import cast, Any

from api_models import (
    GenRequest, GenResponse, TaskProgress, CheckStatus, Task as APITask, Submission as ApiSubmission, SubmissionStatus,
    TaskStatus as ApiTaskStatus, Round, RoundTaskType
)
from back.firebase_db import get_firestore_db
from back.firebase_models import TaskDocument, SubmissionDocument, RoundDocument
from back.taskgen_client import TaskGenClient

class TaskService:
    def __init__(self) -> None:
        self.db = get_firestore_db()
        self.task_gen_client = TaskGenClient()

    def list_tasks_for_team(self, team_id: str, challenge_id: str,
                             status: ApiTaskStatus | None = None,
                             task_type: str | None = None,
                             round_id: str | None = None,
                             since: datetime | None = None) -> list[APITask]:
        """List tasks for a team with optional filters using Firestore queries (no round/task enumeration)."""
        challenge_ref = self.db.collection('challenges').document(challenge_id)
        if not challenge_ref.get().exists:
            return []

        # Build query: either scoped to a round, or across the challenge via collection group
        if round_id:
            q = challenge_ref.collection('rounds').document(round_id).collection('tasks').where('team_id', '==', team_id)
        else:
            q = self.db.collection_group('tasks').where('challenge_id', '==', challenge_id).where('team_id', '==', team_id)

        if task_type is not None:
            q = q.where('type', '==', task_type)
        if since is not None:
            q = q.where('claimed_at', '>=', since)

        snapshots = list(q.stream())
        # Map to APITask using comprehensions; apply status filter client-side supporting enum or string
        from datetime import datetime, timezone
        def to_api(snap: Any) -> APITask:
            d = cast(dict[str, Any], snap.to_dict())
            return APITask(
                id=cast(str, snap.id),
                type=d['type'],
                status=ApiTaskStatus(d['status']),
                score=d.get('score', 0),
                statement=d['statement'],
                input=d.get('input', ''),
                claimed_at=d['claimed_at'],
                submissions=[],
                last_attempt_at=d['claimed_at'],
                solved_at=d.get('solved_at')
            )
        def status_matches(snap: Any) -> bool:
            if status is None:
                return True
            doc = cast(dict[str, Any], snap.to_dict())
            doc_status = doc.get('status')
            return bool(doc_status == status or doc_status == getattr(status, 'value', None))
        filtered = [s for s in snapshots if status_matches(s)]
        tasks = [to_api(s) for s in filtered]
        tasks.sort(key=lambda t: (t.claimed_at or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
        return tasks[:20]


    def get_task(self, task_id: str, challenge_id: str, round_id: str | None = None) -> TaskDocument | None:
        """Get a specific task"""
        challenge_ref = self.db.collection('challenges').document(challenge_id)
        if not challenge_ref.get().exists:
            return None

        rounds_ref = challenge_ref.collection('rounds')
        # Fast path: if round_id is provided, avoid iterating rounds
        if round_id:
            t_ref = rounds_ref.document(round_id).collection('tasks').document(task_id)
            t_doc = t_ref.get()
            if t_doc.exists:
                return TaskDocument.model_validate(t_doc.to_dict())
            return None
        # Fallback: use collection group query to find the task by id under this challenge
        cg = self.db.collection_group('tasks').where('challenge_id', '==', challenge_id).where('id', '==', task_id).limit(1)
        snaps = list(cg.stream())
        if snaps:
            return TaskDocument.model_validate(cast(dict[str, Any], snaps[0].to_dict()))
        return None

    def create_task(self, challenge_id: str, team_id: str, task_type: str | None) -> APITask:
        """Create a new task for a team"""
        # Get challenge and validate current round
        challenge_ref = self.db.collection('challenges').document(challenge_id)
        challenge_doc = challenge_ref.get()

        if not challenge_doc.exists:
            raise ValueError("Challenge not found")

        challenge_data = challenge_doc.to_dict()

        # Find current active round from subcollection using query
        rounds_ref = challenge_ref.collection('rounds')
        rd_snaps = list(rounds_ref.where('published', '==', True).limit(1).stream())
        if not rd_snaps:
            raise ValueError("No active round found for this challenge")
        rd_snap = rd_snaps[0]
        current_round = rd_snap.to_dict()
        current_round_id = rd_snap.id

        if not current_round:
            raise ValueError("No active round found for this challenge")

        # Validate round timing (support both 'start'/'end' and 'start_time'/'end_time' keys)
        current_time = datetime.now(timezone.utc)
        round_start = current_round.get('start') or current_round.get('start_time')
        round_end = current_round.get('end') or current_round.get('end_time')
        if round_start is None or round_end is None:
            raise ValueError("Round timing is not configured")
        if current_time < round_start:
            raise ValueError("Round has not started yet")
        if current_time > round_end:
            raise ValueError("Round has already ended")

        # Validate task type exists in round via subcollection query
        tt_col = rounds_ref.document(current_round_id).collection('task_types')
        tt_snaps = list(tt_col.where('type', '==', task_type).limit(1).stream())
        if not tt_snaps:
            raise ValueError(f"Task type '{task_type}' is not available in this round")
        task_type_data = tt_snaps[0].to_dict()

        # Check task limits
        assert current_round_id is not None
        existing_count = self.get_existing_tasks(team_id, challenge_id, current_round_id, task_type)
        max_tasks = task_type_data.get('tasks_count', 100)

        if existing_count >= max_tasks:
            raise ValueError(f"Maximum number of tasks of type '{task_type}' already taken")

        # Validate team exists using subcollection
        team_doc = challenge_ref.collection('teams').document(team_id).get()
        if not team_doc.exists:
            raise ValueError("Team not found")

        # Load team name for generator context
        team_payload = team_doc.to_dict()
        team_data = {'id': team_id, 'name': team_payload.get('name', team_id)}

        # Generate task ID
        task_id = f"task_{uuid.uuid4().hex[:8]}"

        # Create task progress info
        task_progress = TaskProgress(
            task_index=existing_count,
            task_count=max_tasks,
            elapsed_time=int((current_time - round_start).total_seconds() / 60),
            total_time=int((round_end - round_start).total_seconds() / 60)
        )

        # Generate task content
        gen_response = self.generate_task_content(
            task_id, team_data, challenge_id, current_round_id, task_type_data, task_progress
        )

        # Create task document
        task_doc = TaskDocument(
            id=task_id,
            challenge_id=challenge_id,
            team_id=team_id,
            round_id=current_round_id,
            type=cast(str, task_type),
            status=ApiTaskStatus.PENDING,
            statement=gen_response.statement,
            input=gen_response.input,
            checker_hint=gen_response.checker_hint,
            score=task_type_data['score'],
            claimed_at=current_time
        )

        # Store task as a document in tasks subcollection for the round
        tasks_ref = rounds_ref.document(current_round_id).collection('tasks')
        tasks_ref.document(task_id).set(task_doc.model_dump())

        return APITask(
            id=task_id,
            type=cast(str, task_type),
            status=ApiTaskStatus.PENDING,
            score=task_type_data['score'],
            statement=gen_response.statement,
            input=gen_response.input,
            claimed_at=current_time,
            submissions=[],
            last_attempt_at=current_time,
            solved_at=None
        )

    def get_random_task_type(self, game_round: Round | RoundDocument, team_id: str) -> RoundTaskType:
        """Pick a task type from the current round (Firestore) that still has remaining quota for the team.
        Returns an API RoundTaskType instance. If none available, raises ValueError.
        """
        challenge_ref = self.db.collection('challenges').document(game_round.challenge_id)
        round_ref = challenge_ref.collection('rounds').document(game_round.id)
        if not round_ref.get().exists:
            raise ValueError("Round not found")

        # Load all task types for the round from subcollection
        types_docs = list(round_ref.collection('task_types').stream())
        if not types_docs:
            raise ValueError("No task types available for this round")

        # Compute remaining quota per type for this team
        from typing import Any
        candidates: list[tuple[dict[str, Any], str, int]] = []  # (task_type_data, doc_id, remaining)
        for tt_doc in types_docs:
            td = tt_doc.to_dict()
            type_code = td.get('type')
            max_per_team = int(td.get('tasks_count', 0))
            taken = self.get_existing_tasks(team_id, game_round.challenge_id, game_round.id, type_code)
            remaining = max(0, max_per_team - taken)
            if remaining > 0:
                candidates.append((td, tt_doc.id, remaining))

        if not candidates:
            raise ValueError("All tasks were already taken for this round")

        # Weighted random selection proportional to remaining
        if len(candidates) == 1:
            chosen_td, chosen_id, _ = candidates[0]
        else:
            weights = [rem for _, _, rem in candidates]
            idx = random.choices(range(len(candidates)), weights=weights, k=1)[0]
            chosen_td, chosen_id, _ = candidates[idx]
        return RoundTaskType.model_validate({
            'id': chosen_id,
            'round_id': game_round.id,
            'type': chosen_td['type'],
            'n_tasks': chosen_td.get('n_tasks', 0),
            'generator_url': chosen_td['generator_url'],
            'generator_settings': chosen_td.get('generator_settings'),
            'generator_secret': chosen_td['generator_secret'],
            'score': chosen_td.get('score', 100),
            'time_to_solve': chosen_td['time_to_solve']
        })


    def get_existing_tasks(self, team_id: str, challenge_id: str, round_id: str, task_type: str | None = None) -> int:
        """Count existing tasks for a team in a round/challenge without retrieving documents."""
        challenge_ref = self.db.collection('challenges').document(challenge_id)
        if not challenge_ref.get().exists:
            return 0
        q = (
            challenge_ref
            .collection('rounds').document(round_id)
            .collection('tasks')
            .where('team_id', '==', team_id)
        )
        if task_type is not None:
            q = q.where('type', '==', task_type)
        # Use aggregation count to avoid downloading docs
        agg = q.count()
        res = agg.get()
        # res is a list of rows; each row is a list of AggregationResult. First cell holds the count.
        if res and isinstance(res[0], list) and res[0]:
            return int(res[0][0].value)
        return 0


    def generate_task_content(self, task_id: str, team_data: dict[str, object], challenge_id: str, round_id: str, 
                             task_type_data: dict[str, object], task_progress: TaskProgress) -> GenResponse:
        """Generate task content by calling the task generator"""
        gen_request = GenRequest(
            challenge=challenge_id,
            team=str(team_data['name']),
            round=round_id,
            task_id=task_id,
            progress=task_progress,
            task_settings=str(task_type_data.get('generator_settings', ''))
        )

        generator_url = str(task_type_data['generator_url'])
        generator_secret = str(task_type_data['generator_secret'])
        return self.task_gen_client.generate_task(
            generator_url,
            generator_secret,
            gen_request
        )

    def submit_task_answer(self, task_id: str, team_id: str, challenge_id: str, round_id: str, answer: str) -> ApiSubmission:
        """Submit an answer for a task. If round_id provided, directly access the task within that round; otherwise scan rounds."""
        challenge_ref = self.db.collection('challenges').document(challenge_id)
        challenge_doc = challenge_ref.get()

        if not challenge_doc.exists:
            raise ValueError("Challenge not found")

        task_data = None
        task_type_data = None
        task_ref = None
        resolved_round_id: str
        rounds_ref = challenge_ref.collection('rounds')

        t_ref = rounds_ref.document(round_id).collection('tasks').document(task_id)
        t_doc = t_ref.get()
        if t_doc.exists:
            task_data = t_doc.to_dict()
            task_ref = t_ref
            resolved_round_id = round_id
            # Verify task belongs to team
            if task_data['team_id'] != team_id:
                raise ValueError("Task does not belong to this team")
            # Load task type configuration from this round only via query
            task_type = task_data['type']
            tt_q = rounds_ref.document(resolved_round_id).collection('task_types').document(task_type)
            task_type_data = tt_q.get().to_dict()
        else:
            raise ValueError("Task not found")
        if not task_data:
            raise ValueError("Task not found")
        if not task_type_data:
            raise ValueError("Task type configuration not found")
        assert isinstance(resolved_round_id, str)

        # Check time limit
        current_time = datetime.now(timezone.utc)
        claimed_at = task_data['claimed_at']
        time_limit_minutes = task_type_data['time_to_solve']
        deadline = claimed_at + timedelta(minutes=time_limit_minutes)

        if current_time > deadline:
            raise ValueError(f"Time limit exceeded. The task had to be solved within {time_limit_minutes} minutes.")

        # Check the answer
        check_response = self.task_gen_client.check_answer(
            task_type_data['generator_url'],
            answer,
            task_data.get('checker_hint', ''),
            task_data.get('input', ''),
            task_id
        )

        # Process the first check result
        check_result = check_response[0]
        submission_id = f"submission_{uuid.uuid4().hex[:8]}"

        # Update task document and write submission into subcollection
        assert task_ref is not None
        if check_result.status == CheckStatus.ACCEPTED:
            # Update task status in task document
            task_ref.update({'status': ApiTaskStatus.AC, 'solved_at': current_time})
            # Calculate score
            score = int(float(task_data['score']) * check_result.score)
            submission_doc = SubmissionDocument(
                id=submission_id,
                challenge_id=challenge_id,
                team_id=team_id,
                round_id=resolved_round_id,
                task_id=task_id,
                status=SubmissionStatus.AC,
                submitted_at=current_time,
                answer=answer,
                checker_output="",
                score=score
            )
        else:
            # Update task status to WA
            task_ref.update({'status': ApiTaskStatus.WA})
            submission_doc = SubmissionDocument(
                id=submission_id,
                challenge_id=challenge_id,
                team_id=team_id,
                round_id=resolved_round_id,
                task_id=task_id,
                status=SubmissionStatus.WA,
                submitted_at=current_time,
                answer=answer,
                checker_output=check_result.error or "",
                score=0
            )

        # Write submission as a document in submissions subcollection under the task
        task_ref.collection('submissions').document(submission_id).set(submission_doc.model_dump())

        return ApiSubmission(
            id=submission_id,
            status=submission_doc.status,
            submitted_at=submission_doc.submitted_at,
            task_id=task_id,
            answer=submission_doc.answer,
            checker_output=submission_doc.checker_output,
            score=submission_doc.score
        )


# Backward‑compat alias for tests that import FirebaseTaskService
class FirebaseTaskService(TaskService):
    pass
