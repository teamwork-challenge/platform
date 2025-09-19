from typing import Dict, Optional, Any

from api_models import Dashboard, TypeStats, AuthData, Leaderboard, TeamScore
from back.db_models import TeamDashboardDocument, RoundDocument
from back.services.db import get_firestore_db
from back.services.team_service import TeamService


class BoardService:

    def __init__(self) -> None:
        self.db = get_firestore_db()

    def get_dashboard(self, auth: AuthData, round_id: Optional[str]) -> Dashboard:
        if auth.challenge_id is None or auth.team_id is None:
            raise ValueError("Invalid team or challenge context")
        resolved_round_id = round_id or (auth.round_id or "")
        if not resolved_round_id:
            raise ValueError("Round not found")

        rd = self.get_round(auth.challenge_id, resolved_round_id)
        dash = self.get_team_dashboard(auth.challenge_id, resolved_round_id, auth.team_id)

        counters: Dict[str, tuple[int, int, int]] = {}
        for dash_tt in dash.task_types:
            counters[dash_tt.task_type] = (dash_tt.ac, dash_tt.wa, dash_tt.pending)

        stats: Dict[str, TypeStats] = {}
        total_ac = total_wa = total_pending = total_remaining = 0

        for round_tt in rd.task_types:
            ac, wa, pending = counters.get(round_tt.type, (0, 0, 0))
            total = ac + wa + pending
            remaining = max(0, round_tt.n_tasks - total)
            stats[round_tt.type] = TypeStats(total=total, pending=pending, ac=ac, wa=wa, remaining=remaining)
            total_ac += ac
            total_wa += wa
            total_pending += pending
            total_remaining += remaining

        return Dashboard(round_id=resolved_round_id, stats=stats)

    def round_ref(self, challenge_id: str, round_id: str) -> Any:
        """Return a Firestore reference to a specific round."""
        return self.db.collection('challenges').document(challenge_id) \
                      .collection('rounds').document(round_id)

    def get_team_dashboard(self, challenge_id: str, round_id: str, team_id: str) -> TeamDashboardDocument:
        dash_ref = self.round_ref(challenge_id, round_id) \
                        .collection('dashboards').document(team_id)
        snap = dash_ref.get()
        if snap.exists:
            return TeamDashboardDocument.model_validate(snap.to_dict())
        return TeamDashboardDocument(team_id=team_id, challenge_id=challenge_id, round_id=round_id, score=0, task_types=[])

    def get_round(self, challenge_id: str, round_id: str) -> RoundDocument:
        rd_doc = self.round_ref(challenge_id, round_id).get()
        if not rd_doc.exists:
            raise ValueError("Round not found")
        return RoundDocument.model_validate(rd_doc.to_dict())

    def get_leaderboard(self, auth: AuthData, round_id: Optional[str]) -> Leaderboard:
        if auth.challenge_id is None:
            raise ValueError("Invalid challenge context")
        resolved_round_id = round_id or (auth.round_id or "")
        if not resolved_round_id:
            raise ValueError("Round not found")

        dash_ref = self.round_ref(auth.challenge_id, resolved_round_id).collection('dashboards')
        docs = list(dash_ref.stream())
        if not docs:
            return Leaderboard(round_id=resolved_round_id, teams=[])

        dashboards: list[TeamDashboardDocument] = [
            TeamDashboardDocument.model_validate(doc.to_dict()) for doc in docs
        ]
        team_service = TeamService()
        existing_teams = team_service.get_teams_by_challenge(auth.challenge_id)
        id_to_name: dict[str, str] = {t.id: t.name for t in existing_teams}

        data: list[tuple[str, int, dict[str, int]]] = []
        for d in dashboards:
            team_name = id_to_name.get(d.team_id, d.team_id)
            type_scores: dict[str, int] = {tt.task_type: int(tt.score) for tt in d.task_types}
            data.append((team_name, int(d.score), type_scores))

        # Sort by total_score desc, then team name asc
        data_sorted = sorted(data, key=lambda t: (-t[1], t[0]))
        lb_teams: list[TeamScore] = [TeamScore(rank=idx, name=name, total_score=score, scores=scores)
                                     for idx, (name, score, scores) in enumerate(data_sorted, start=1)]
        return Leaderboard(round_id=resolved_round_id, teams=lb_teams)
