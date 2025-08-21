from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import cast, Any

from api_models import (
    GenRequest, GenResponse, TaskProgress, CheckStatus, Task as APITask, Submission as ApiSubmission, SubmissionStatus,
    TaskStatus as ApiTaskStatus, Round, RoundTaskType
)
from back.services.db import get_firestore_db
from back.db_models import TaskDocument, SubmissionDocument, RoundDocument, TaskTypeDocument, TeamDashboardDocument, TeamTaskDashboardDocument
from back.services.taskgen_client import TaskGenClient
from google.cloud import firestore as gcs_firestore


class TaskService:
    def __init__(self) -> None:
        self.db = get_firestore_db()
        self.task_gen_client = TaskGenClient()

    def list_tasks_for_team(self, team_id: str, challenge_id: str,
                             status: ApiTaskStatus | None = None,
                             task_type: str | None = None,
                             round_id: str | None = None,
                             since: datetime | None = None) -> list[APITask]:
        """List tasks for a team with optional filters scoped to a specific round. No fallbacks."""
        if round_id is None:
            return []
        challenge_ref = self.db.collection('challenges').document(challenge_id)
        if not challenge_ref.get().exists:
            return []

        q = challenge_ref.collection('rounds').document(round_id).collection('tasks').where('team_id', '==', team_id)

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


    def get_task(self, task_id: str, challenge_id: str, round_id: str) -> TaskDocument | None:
        """Get a specific task under a known challenge/round. No fallbacks."""
        challenge_ref = self.db.collection('challenges').document(challenge_id)
        if not challenge_ref.get().exists:
            return None
        t_ref = challenge_ref.collection('rounds').document(round_id).collection('tasks').document(task_id)
        t_doc = t_ref.get()
        if t_doc.exists:
            return TaskDocument.model_validate(t_doc.to_dict())
        return None

    def create_task(self, challenge_id: str, round_id: str, team_id: str, task_type: str | None) -> APITask:
        """Create a new task for a team in the specified round. No auto-current fallbacks."""
        # Get challenge and the specific round
        challenge_ref = self.db.collection('challenges').document(challenge_id)
        challenge_doc = challenge_ref.get()
        if not challenge_doc.exists:
            raise ValueError("Challenge not found")

        rounds_ref = challenge_ref.collection('rounds')
        rd_doc = rounds_ref.document(round_id).get()
        if not rd_doc.exists:
            raise ValueError("Round not found")
        current_round = RoundDocument.model_validate(rd_doc.to_dict())
        current_round_id = current_round.id

        # Validate round timing (support both 'start'/'end' and 'start_time'/'end_time' keys) and published flag
        current_time = datetime.now(timezone.utc)
        round_start = current_round.start_time
        round_end = current_round.end_time
        if not current_round.published:
            raise ValueError("Round is not published")
        if current_time < round_start:
            raise ValueError("Round has not started yet")
        if current_time > round_end:
            raise ValueError("Round has already ended")

        task_type_data = self.get_task_type(current_round, task_type, team_id)
        if task_type_data is None:
            raise ValueError("No task type found")

        # For task progress, peek at dashboard to estimate the index (not authoritative; limit enforced in TX)
        dash = self._get_team_dashboard(challenge_id, current_round_id, team_id)
        taken_count = 0
        for t in dash.task_types:
            if t.task_type == task_type_data.type:
                taken_count = t.ac + t.wa + t.pending
                break

        # Generate task ID
        task_id = f"task_{uuid.uuid4().hex[:8]}"

        # Create task progress info
        task_progress = TaskProgress(
            task_index=taken_count,
            task_count=task_type_data.n_tasks,
            elapsed_time=int((current_time - round_start).total_seconds() / 60),
            total_time=int((round_end - round_start).total_seconds() / 60)
        )

        # Generate task content
        gen_response = self.generate_task_content(
            task_id, team_id, challenge_id, current_round_id, task_type_data, task_progress)

        # Create task document
        task_doc = TaskDocument(
            id=task_id,
            challenge_id=challenge_id,
            team_id=team_id,
            round_id=current_round_id,
            type=task_type_data.type,
            status=ApiTaskStatus.PENDING,
            statement=gen_response.statement,
            input=gen_response.input,
            checker_hint=gen_response.checker_hint,
            score=0,
            claimed_at=current_time
        )

        # Atomically create the task and update the dashboard within a single transaction
        tasks_ref = rounds_ref.document(current_round_id).collection('tasks')
        dash_ref = rounds_ref.document(current_round_id).collection('dashboards').document(team_id)

        from google.cloud import firestore as gcs_firestore
        db_client = self.db

        @gcs_firestore.transactional # type: ignore[misc]
        def _do_create(tx: Any) -> None:
            snap = dash_ref.get(transaction=tx)
            if snap.exists:
                dash_local = TeamDashboardDocument.model_validate(snap.to_dict())
            else:
                dash_local = TeamDashboardDocument(team_id=team_id, challenge_id=challenge_id, round_id=current_round_id, score=0, task_types=[])
            # recompute taken_count in-transaction to enforce limit under concurrency
            taken_local = 0
            found_local = None
            for tt in dash_local.task_types:
                if tt.task_type == task_type_data.type:
                    taken_local = tt.ac + tt.wa + tt.pending
                    found_local = tt
                    break
            if taken_local >= task_type_data.n_tasks:
                raise ValueError(f"Maximum number of tasks of type '{task_type_data.type}' already taken")
            # Write task document
            tx.set(tasks_ref.document(task_id), task_doc.model_dump())
            # Update dashboard counters: pending++ for this type
            if found_local is not None:
                found_local.pending += 1
            else:
                dash_local.task_types.append(TeamTaskDashboardDocument(task_type=task_type_data.type, score=0, ac=0, wa=0, pending=1))
            tx.set(dash_ref, dash_local.model_dump())
        _do_create(db_client.transaction(max_attempts=1))

        return APITask.model_validate(task_doc, from_attributes=True)

    def get_task_type(self, current_round: RoundDocument, task_type: str | None, team_id: str) -> TaskTypeDocument | None:
        task_type = task_type or self.get_random_task_type(current_round, team_id).type
        return current_round.get_task_type(task_type)


    def _get_team_dashboard(self, challenge_id: str, round_id: str, team_id: str) -> TeamDashboardDocument:
        """Fetch or initialize the TeamDashboardDocument for a team/round."""
        dash_ref = (self.db.collection('challenges').document(challenge_id)
                    .collection('rounds').document(round_id)
                    .collection('dashboards').document(team_id))
        snap = dash_ref.get()
        if snap.exists:
            return TeamDashboardDocument.model_validate(snap.to_dict())
        # If missing, initialize with zeroes (no task types until needed)
        return TeamDashboardDocument(team_id=team_id, challenge_id=challenge_id, round_id=round_id, score=0, task_types=[])

    def _get_remaining_by_type(self, rd: RoundDocument, dash: TeamDashboardDocument) -> list[tuple[TaskTypeDocument, int]]:
        # Build a map of counts from dashboard
        counts: dict[str, int] = {}
        for t in dash.task_types:
            # number taken = ac + wa + pending
            counts[t.task_type] = t.ac + t.wa + t.pending
        candidates: list[tuple[TaskTypeDocument, int]] = []
        for tt in rd.task_types:
            taken = counts.get(tt.type, 0)
            remaining = max(0, tt.n_tasks - taken)
            if remaining > 0:
                candidates.append((tt, remaining))
        return candidates

    def get_random_task_type(self, game_round: Round | RoundDocument, team_id: str) -> TaskTypeDocument:
        """Pick a task type using the per-team dashboard counters instead of scanning tasks."""
        challenge_ref = self.db.collection('challenges').document(game_round.challenge_id)
        round_ref = challenge_ref.collection('rounds').document(game_round.id)
        if not round_ref.get().exists:
            raise ValueError("Round not found")
        rd_doc = round_ref.get()
        if not rd_doc.exists:
            raise ValueError("Round not found")
        rd = RoundDocument.model_validate(rd_doc.to_dict())
        dash = self._get_team_dashboard(game_round.challenge_id, game_round.id, team_id)
        candidates = self._get_remaining_by_type(rd, dash)
        if not candidates:
            raise ValueError("All tasks were already taken for this round")
        if len(candidates) == 1:
            chosen_td, _ = candidates[0]
        else:
            weights = [rem for _, rem in candidates]
            idx = random.choices(range(len(candidates)), weights=weights, k=1)[0]
            chosen_td, _ = candidates[idx]
        return chosen_td




    def generate_task_content(self, task_id: str, challenge_id: str, round_id: str, team_id: str,
                             task_type_data: TaskTypeDocument, task_progress: TaskProgress) -> GenResponse:
        """Generate task content by calling the task generator"""
        gen_request = GenRequest(
            challenge_id=challenge_id,
            team_id=team_id,
            round_id=round_id,
            task_id=task_id,
            progress=task_progress,
            task_settings=task_type_data.generator_settings
        )

        generator_url = task_type_data.generator_url
        generator_secret = task_type_data.generator_secret
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

        task = None
        resolved_round_id: str
        rounds_ref = challenge_ref.collection('rounds')

        t_ref = rounds_ref.document(round_id).collection('tasks').document(task_id)
        t_doc = t_ref.get()
        if t_doc.exists:
            task = TaskDocument.model_validate(t_doc.to_dict())
            task_ref = t_ref
            resolved_round_id = round_id
            # Verify task belongs to team
            if task.team_id != team_id:
                raise ValueError("Task does not belong to this team")
            task_type = task.type
            r_doc = rounds_ref.document(resolved_round_id).get()
            round = RoundDocument.model_validate(r_doc.to_dict())
            task_type_doc = round.get_task_type(task_type)
        else:
            raise ValueError("Task not found")
        if task_type_doc is None:
            raise ValueError("Task type not found")

        # Check time limit
        current_time = datetime.now(timezone.utc)
        claimed_at = task.claimed_at
        time_limit_minutes = task_type_doc.time_to_solve
        deadline = claimed_at + timedelta(minutes=time_limit_minutes)

        if current_time > deadline:
            raise ValueError(f"Time limit exceeded. The task had to be solved within {time_limit_minutes} minutes.")

        # Check the answer
        check_response = self.task_gen_client.check_answer(
            task_type_doc.generator_url,
            answer,
            task.checker_hint,
            task.input,
            task_id
        )

        # Process the first check result
        check_result = check_response[0]
        submission_id = f"submission_{uuid.uuid4().hex[:8]}"

        # Update task document and write submission into subcollection
        assert task_ref is not None
        # Prepare dashboard refs
        dash_ref = rounds_ref.document(resolved_round_id).collection('dashboards').document(team_id)
        if check_result.status == CheckStatus.ACCEPTED:
            # Update task status in task document
            task_ref.update({'status': ApiTaskStatus.AC, 'solved_at': current_time})
            # Calculate score
            calc_score = int(float(task_type_doc.score) * check_result.score)
            # Update dashboard within a transaction: pending--, ac++, score+=
            snap = dash_ref.get()
            if snap.exists:
                dash = TeamDashboardDocument.model_validate(snap.to_dict())
            else:
                dash = TeamDashboardDocument(team_id=team_id, challenge_id=challenge_id, round_id=resolved_round_id, score=0, task_types=[])
            # update totals
            dash.score += calc_score
            found = False
            for t in dash.task_types:
                if t.task_type == task_type_doc.type:
                    t.pending = max(0, t.pending - 1)
                    t.ac += 1
                    t.score += calc_score
                    found = True
                    break
            if not found:
                dash.task_types.append(TeamTaskDashboardDocument(task_type=task_type_doc.type, score=calc_score, ac=1, wa=0, pending=0))
            dash_ref.set(dash.model_dump())
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
                score=calc_score
            )
        else:
            # Update task status to WA
            task_ref.update({'status': ApiTaskStatus.WA})
            # Update dashboard within a transaction: pending--, wa++
            snap = dash_ref.get()
            if snap.exists:
                dash = TeamDashboardDocument.model_validate(snap.to_dict())
            else:
                dash = TeamDashboardDocument(team_id=team_id, challenge_id=challenge_id, round_id=resolved_round_id, score=0, task_types=[])
            found = False
            for t in dash.task_types:
                if t.task_type == task_type_doc.type:
                    t.pending = max(0, t.pending - 1)
                    t.wa += 1
                    found = True
                    break
            if not found:
                dash.task_types.append(TeamTaskDashboardDocument(task_type=task_type_doc.type, score=0, ac=0, wa=1, pending=0))
            dash_ref.set(dash.model_dump())
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

    def list_submissions_for_task(self, challenge_id: str, round_id: str, task_id: str) -> list[ApiSubmission]:
        """List submissions for a specific task (ordered by submitted_at desc)."""
        task_ref = (self.db.collection('challenges').document(challenge_id)
                    .collection('rounds').document(round_id)
                    .collection('tasks').document(task_id))
        t_doc = task_ref.get()
        if not t_doc.exists:
            return []
        subs = list(task_ref.collection('submissions').order_by('submitted_at', direction=gcs_firestore.Query.DESCENDING).stream())
        result: list[ApiSubmission] = []
        for s in subs:
            d = SubmissionDocument.model_validate(s.to_dict())
            result.append(ApiSubmission(
                id=d.id,
                status=d.status,
                submitted_at=d.submitted_at,
                task_id=d.task_id,
                answer=d.answer,
                checker_output=d.checker_output,
                score=d.score
            ))
        return result

    def get_last_submission_for_team(self, challenge_id: str, round_id: str, team_id: str) -> ApiSubmission | None:
        """Get the most recent submission for a specific team within a round."""
        q = (self.db.collection_group('submissions')
             .where('challenge_id', '==', challenge_id)
             .where('round_id', '==', round_id)
             .where('team_id', '==', team_id)
             .order_by('submitted_at', direction=gcs_firestore.Query.DESCENDING)
             .limit(1))
        docs = list(q.stream())
        if not docs:
            return None
        d = SubmissionDocument.model_validate(docs[0].to_dict())
        return ApiSubmission(
            id=d.id,
            status=d.status,
            submitted_at=d.submitted_at,
            task_id=d.task_id,
            answer=d.answer,
            checker_output=d.checker_output,
            score=d.score
        )

    def get_last_submission_for_all_teams(self, challenge_id: str, round_id: str) -> dict[str, ApiSubmission]:
        """Get the most recent submission per team within a round (admin only)."""
        # Fetch recent submissions and fold by team_id keeping latest
        q = (self.db.collection_group('submissions')
             .where('challenge_id', '==', challenge_id)
             .where('round_id', '==', round_id)
             .order_by('submitted_at', direction=gcs_firestore.Query.DESCENDING)
             .limit(1000))
        latest: dict[str, ApiSubmission] = {}
        for doc in q.stream():
            d = SubmissionDocument.model_validate(doc.to_dict())
            if d.team_id not in latest:
                latest[d.team_id] = ApiSubmission(
                    id=d.id,
                    status=d.status,
                    submitted_at=d.submitted_at,
                    task_id=d.task_id,
                    answer=d.answer,
                    checker_output=d.checker_output,
                    score=d.score
                )
        return latest


# Backward‑compat alias for tests that import FirebaseTaskService
class FirebaseTaskService(TaskService):
    pass
