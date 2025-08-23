import logging
import os
import concurrent.futures
import sys
import time
from typing import Iterator
import pytest
from pathlib import Path

from cli.api_client import ApiClient
from cli.config_manager import ConfigManager
from api_models import (
    SubmitAnswerRequest,
    Challenge,
    Round,
    RoundTaskType,
)

# Real backend URL
REAL_BACKEND_URL = os.environ.get("TWCHALLENGE_URL", "https://twchallenge-back-251082000975.europe-west1.run.app")
# Use env override for admin key if needed; default to the seeded key name
STRESS_ADMIN_KEY = os.environ.get("TWCHALLENGE_ADMIN_KEY", "twc-admin-9c446f9d0456f5e22f47da")


@pytest.fixture(scope="module", autouse=True)
def stress_server() -> Iterator[None]:
    # Ensure project root cwd
    project_root = Path(__file__).resolve().parents[1]
    os.chdir(project_root)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # nuke prior handlers so this actually applies
    )


    # Prepare dedicated test challenge and a fresh round
    cache_dir = Path('.pytest_cache')
    cache_dir.mkdir(exist_ok=True)

    admin_cfg = ConfigManager(cache_dir / 'stress_admin_real.json')
    admin_client = ApiClient(admin_cfg)
    admin_client.save_api_key(STRESS_ADMIN_KEY)
    admin_cfg.save_base_url(REAL_BACKEND_URL)

    challenge_id = "stress_test"
    round_id = "stress_round"

    # 1) Ensure the challenge exists and points to the planned round
    ch = Challenge(id=challenge_id, title="Stress Test", description="Ephemeral stress test challenge", current_round_id=round_id)
    admin_client.put_challenge(ch)

    # 2) Delete only THIS challenge’s rounds to start clean (no global cleanup)
    try:
        for rd in admin_client.list_rounds(challenge_id):
            admin_client.delete_round(challenge_id, rd.id)
    except Exception:
        # If the challenge was just created and has no rounds yet, ignore
        pass

    # 3) Create the fresh round with a_plus_b generator pointing to the backend’s internal task generator
    #    The taskgen endpoints are served by the backend under /task_gen and secured via X-API-Key "secret"
    tt = RoundTaskType(
        type="a_plus_b",
        n_tasks=1000,
        generator_url=f"{REAL_BACKEND_URL}/task_gen/a_plus_b",
        generator_settings="",
        generator_secret="secret",
        score=100,
        time_to_solve=30,
        score_decay_with_time=False,
        n_attempts=100,
    )

    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    rd = Round(
        id=round_id,
        challenge_id=challenge_id,
        published=True,
        start_time=now - timedelta(minutes=1),
        end_time=now + timedelta(hours=6),
        claim_by_type=True,
        task_types=[tt],
    )
    admin_client.update_round(rd)

    try:
        yield
    finally:
        # Leave the challenge in place; we only cleaned its rounds at start
        pass


def test_stress_claim() -> None:
    # Two teams work in parallel in the same round, claiming tasks and submitting the answers.
    cache_dir = Path('.pytest_cache')
    cache_dir.mkdir(exist_ok=True)

    # Admin client on the real backend
    admin_cfg = ConfigManager(cache_dir / 'stress_admin.json')
    admin_cfg.save_base_url(REAL_BACKEND_URL)
    admin_client = ApiClient(admin_cfg)
    admin_client.save_api_key(STRESS_ADMIN_KEY)


    from api_models import TeamsImportRequest, TeamCreateRequest

    # Create two teams inside the dedicated test challenge
    req = TeamsImportRequest(
        challenge_id='stress_test',
        teams=[
            TeamCreateRequest(name='Stress Team A', members='A', captain_contact='@a'),
            TeamCreateRequest(name='Stress Team B', members='B', captain_contact='@b'),
        ]
    )
    import_resp = admin_client.create_teams(req)
    assert len(import_resp.teams) == 2
    teamA_key = import_resp.teams[0].api_key
    teamB_key = import_resp.teams[1].api_key

    # Separate clients for each team
    a_cfg = ConfigManager(cache_dir / 'stress_team_a.json')
    a_cfg.save_base_url(REAL_BACKEND_URL)
    b_cfg = ConfigManager(cache_dir / 'stress_team_b.json')
    b_cfg.save_base_url(REAL_BACKEND_URL)
    client_a = ApiClient(a_cfg)
    client_a.save_api_key(teamA_key)
    client_b = ApiClient(b_cfg)
    client_b.save_api_key(teamB_key)

    # Claim and solve N tasks of type a_plus_b
    N = 20

    def solve_tasks(client: ApiClient, n: int) -> list[str]:
        solved_task_ids: list[str] = []
        for _ in range(n):
            task = client.claim_task(task_type='a_plus_b', challenge_id='stress_test', round_id='stress_round')
            # The generator produces "1 2" as input; 1+2 == 3
            sub_req = SubmitAnswerRequest(task_id=task.id, answer="3")
            sub = client.submit_task_answer(sub_req, challenge_id='stress_test', round_id='stress_round')
            assert sub.status.value == 'ac'
            solved_task_ids.append(task.id)
        return solved_task_ids

    # Run in parallel for two teams
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        fut_a = ex.submit(solve_tasks, client_a, N)
        fut_b = ex.submit(solve_tasks, client_b, N)
        ids_a = fut_a.result(timeout=6000)
        ids_b = fut_b.result(timeout=6000)

    print("Successfully solved tasks for Team A: ", len(ids_a))
    print("Successfully solved tasks for Team B: ", len(ids_b))

    assert set(ids_a).isdisjoint(set(ids_b))


def test_stress_claim_3workers() -> None:
    # Three workers: Team A single worker; Team B two workers in parallel (may cause transaction conflicts)
    cache_dir = Path('.pytest_cache')
    cache_dir.mkdir(exist_ok=True)

    admin_cfg = ConfigManager(cache_dir / 'stress_admin_3w.json')
    admin_cfg.save_base_url(REAL_BACKEND_URL)
    admin_client = ApiClient(admin_cfg)
    admin_client.save_api_key(STRESS_ADMIN_KEY)

    from api_models import TeamsImportRequest, TeamCreateRequest

    req = TeamsImportRequest(
        challenge_id='stress_test',
        teams=[
            TeamCreateRequest(name='Stress3W Team A', members='A', captain_contact='@a'),
            TeamCreateRequest(name='Stress3W Team B', members='B', captain_contact='@b'),
        ]
    )
    import_resp = admin_client.create_teams(req)
    assert len(import_resp.teams) == 2
    teamA_key = import_resp.teams[0].api_key
    teamB_key = import_resp.teams[1].api_key

    # Clients
    a_cfg = ConfigManager(cache_dir / 'stress3w_team_a.json')
    a_cfg.save_base_url(REAL_BACKEND_URL)
    b1_cfg = ConfigManager(cache_dir / 'stress3w_team_b1.json')
    b1_cfg.save_base_url(REAL_BACKEND_URL)
    b2_cfg = ConfigManager(cache_dir / 'stress3w_team_b2.json')
    b2_cfg.save_base_url(REAL_BACKEND_URL)

    client_a = ApiClient(a_cfg)
    client_a.save_api_key(teamA_key)
    client_b1 = ApiClient(b1_cfg)
    client_b1.save_api_key(teamB_key)
    client_b2 = ApiClient(b2_cfg)
    client_b2.save_api_key(teamB_key)

    N = 9  # total B will do N using 3 workers

    def solve_tasks_no_retry(client: ApiClient, n: int) -> list[str]:
        ids: list[str] = []
        for _ in range(n):
            task = client.claim_task(task_type='a_plus_b', challenge_id='stress_test', round_id='stress_round')
            parts = (task.input or '').strip().split()
            a = int(parts[0]) if len(parts) > 0 else 0
            b = int(parts[1]) if len(parts) > 1 else 0
            ans = str(a + b)
            sub = client.submit_task_answer(SubmitAnswerRequest(task_id=task.id, answer=ans), challenge_id='stress_test', round_id='stress_round')
            assert sub.status.value == 'ac'
            ids.append(task.id)
        return ids

    def solve_tasks_with_retry(client: ApiClient, n: int, max_tries: int = 20) -> int:
        ids: list[str] = []
        attempts = 0
        while len(ids) < n:
            try:
                task = client.claim_task(task_type='a_plus_b', challenge_id='stress_test', round_id='stress_round')
            except Exception:
                attempts += 1
                if attempts > max_tries * n:
                    return attempts
                continue
            while True:
                try:
                    sub = client.submit_task_answer(SubmitAnswerRequest(task_id=task.id, answer="3"), challenge_id='stress_test', round_id='stress_round')
                    break
                except Exception:
                    attempts += 1
                    if attempts > max_tries * n:
                        return attempts
            assert sub.status.value == 'ac'
            ids.append(task.id)
        return attempts

    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        each = N // 3 if N % 3 == 0 else (N // 3)
        fut_b1 = ex.submit(solve_tasks_with_retry, client_b1, each, each)
        fut_b2 = ex.submit(solve_tasks_with_retry, client_b2, each, each)
        fut_b3 = ex.submit(solve_tasks_with_retry, client_b2, N - 2*each, N - 2*each)
        fut_a = ex.submit(solve_tasks_no_retry, client_a, N)
        ids_a = fut_a.result(timeout=1200)
        duration = time.time() - start
        att1 = fut_b1.result(timeout=1200)
        att2 = fut_b2.result(timeout=1200)
        att3 = fut_b3.result(timeout=1200)
        durationB = time.time() - start

    assert len(ids_a) == N
    print(f"Team A solved {N} tasks in {duration:.2f} seconds")
    print(f"Concurrent Team B workers had {att1}, {att2} and {att3} retries; total duration {durationB:.2f} seconds")

    # Allow a bit more headroom on a remote backend
    assert duration < N*2
