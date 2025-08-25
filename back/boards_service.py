from typing import Dict

from sqlalchemy import select
from sqlalchemy.orm import Session

from api_models import Dashboard as ApiDashboard, TypeStats as ApiTypeStats, TaskStatus as ApiTaskStatus
from back.db_models import RoundTaskType, Dashboard, Task


class BoardsService:
    def __init__(self, db: Session):
        self.db = db

    def add_task_to_dashboard(self, task: Task, round_task_type: RoundTaskType) -> None:
        row = self.db.execute(
            select(Dashboard).where(
                (Dashboard.round_id == task.round_id)
                & (Dashboard.team_id == task.team_id)
                & (Dashboard.round_task_type_id == task.round_task_type_id)
            )
        ).scalar_one_or_none()
        if row is None:
            remaining_value = round_task_type.max_tasks_per_team
            row = Dashboard(
                round_id=task.round_id,
                team_id=task.team_id,
                round_task_type_id=task.round_task_type_id,
                type=round_task_type.type,
                pending=0,
                ac=0,
                wa=0,
                remaining=remaining_value,
            )
            self.db.add(row)
        # when task is created: increase pending and recompute remaining using max_tasks_per_team - total
        row.pending += 1
        if round_task_type.max_tasks_per_team is not None:
            total = row.pending + row.ac + row.wa
            row.remaining = round_task_type.max_tasks_per_team - total
        else:
            row.remaining = 0

    def update_dashboard(self, task: Task, prev_status: ApiTaskStatus, new_status: ApiTaskStatus) -> None:
        # Update dashboard counters according to transition rules
        row = self.db.execute(
            select(Dashboard).where(
                (Dashboard.round_id == task.round_id)
                & (Dashboard.team_id == task.team_id)
                & (Dashboard.round_task_type_id == task.round_task_type_id)
            )
        ).scalar_one_or_none()
        if row is None:
            return
        # Apply transition
        if prev_status != new_status:
            if prev_status == ApiTaskStatus.PENDING and new_status == ApiTaskStatus.AC:
                row.pending -= 1
                row.ac += 1
            elif prev_status == ApiTaskStatus.PENDING and new_status == ApiTaskStatus.WA:
                row.pending -= 1
                row.wa += 1
            elif prev_status == ApiTaskStatus.WA and new_status == ApiTaskStatus.AC:
                row.wa -= 1
                row.ac += 1
        # WA->WA or AC->AC (and AC sticky preventing AC->WA) => no changes

    def get_dashboard(self, team_id: int, round_id: int) -> ApiDashboard:
        # Load dashboard stats for the team in the round
        dashboard_rows = list(
            self.db.execute(
                select(Dashboard)
                .where((Dashboard.team_id == team_id) & (Dashboard.round_id == round_id))
                .order_by(Dashboard.round_task_type_id.asc())
            ).scalars().all()
        )

        # Load all task types for the round to include even those with zero tasks
        rtt_list = list(
            self.db.execute(
                select(RoundTaskType)
                .where(RoundTaskType.round_id == round_id)
                .order_by(RoundTaskType.id.asc())
            ).scalars().all()
        )

        # Build stats dictionary from dashboard rows
        stats: Dict[str, ApiTypeStats] = {}
        dashboard_by_type = {row.type: row for row in dashboard_rows}

        # Ensure we include all round task types, even with zero tasks
        for rtt in rtt_list:
            dashboard_row = dashboard_by_type.get(rtt.type)

            if dashboard_row:
                # Use pre-calculated values from dashboard
                stats[rtt.type] = ApiTypeStats(
                    pending=dashboard_row.pending,
                    ac=dashboard_row.ac,
                    wa=dashboard_row.wa,
                    remaining=dashboard_row.remaining
                )
            else:
                # No tasks of this type yet - create zero stats
                stats[rtt.type] = ApiTypeStats(
                    pending=0,
                    ac=0,
                    wa=0,
                    remaining=rtt.max_tasks_per_team
                )

        return ApiDashboard(round_id=round_id, stats=stats)
