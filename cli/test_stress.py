import os
import concurrent.futures
import time
import random
from time import sleep
from typing import List, Tuple, Iterator
import pytest
from pathlib import Path
import subprocess
import requests
from requests.exceptions import RequestException

from cli.api_client import ApiClient
from cli.config_manager import ConfigManager
from api_models import SubmitAnswerRequest
from back.tests.test_setup import clear_firestore_data, create_test_firebase_data

backend_port = 8918


def _wait_endpoint_up(server_url: str, max_wait_time: float = 2.0) -> None:
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        try:
            r = requests.get(server_url, timeout=0.5)
            if r.status_code == 200:
                return
        except RequestException:
            time.sleep(0.1)


@pytest.fixture(scope="module", autouse=True)
def stress_server() -> Iterator[None]:
    # ensure project root cwd
    project_root = Path(__file__).resolve().parents[1]
    os.chdir(project_root)
    os.environ["CHALLENGE_API_URL"] = f"http://127.0.0.1:{backend_port}"
    os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8080"
    clear_firestore_data()
    create_test_firebase_data()
    proc = subprocess.Popen(["uvicorn", "back.main:app", "--port", str(backend_port)])
    _wait_endpoint_up(f"http://127.0.0.1:{backend_port}")
    # initialize ApiClient with a temp config under project .pytest_cache to avoid user home
    try:
        yield
    finally:
        proc.terminate()
        proc.wait()


@pytest.mark.timeout(15)
def test_stress_claim() -> None:
    # two teams work in parallel in the same round, claiming tasks and submitting the answers.
    # Use ApiClient to interact with back. Each team has its own client.
    # 1) Create two teams in challenge_1 via admin API to ensure same round
    cache_dir = Path('.pytest_cache')
    cache_dir.mkdir(exist_ok=True)

    # Admin client
    admin_cfg = ConfigManager(cache_dir / 'stress_admin.json')
    admin_client = ApiClient(admin_cfg)
    admin_client.save_api_key('admin1')  # seeded in create_test_firebase_data

    from api_models import TeamsImportRequest, TeamCreateRequest

    req = TeamsImportRequest(
        challenge_id='challenge_1',
        teams=[
            TeamCreateRequest(name='Stress Team A', members='A', captain_contact='@a'),
            TeamCreateRequest(name='Stress Team B', members='B', captain_contact='@b'),
        ]
    )
    import_resp = admin_client.create_teams(req)
    assert len(import_resp.teams) == 2
    teamA_key = import_resp.teams[0].api_key
    teamB_key = import_resp.teams[1].api_key

    # 2) Prepare two separate clients with isolated configs
    a_cfg = ConfigManager(cache_dir / 'stress_team_a.json')
    b_cfg = ConfigManager(cache_dir / 'stress_team_b.json')
    client_a = ApiClient(a_cfg)
    client_a.save_api_key(teamA_key)
    client_b = ApiClient(b_cfg)
    client_b.save_api_key(teamB_key)

    # 3) Define worker: claim and solve N tasks of type a_plus_b
    N = 20

    def solve_tasks(client: ApiClient, n: int) -> list[str]:
        solved_task_ids: list[str] = []
        for _ in range(n):
            # Claim a task of specific type to avoid unsupported generators
            task = client.claim_task(task_type='a_plus_b')
            sub_req = SubmitAnswerRequest(task_id=task.id, answer="3")
            sub = client.submit_task_answer(sub_req)
            assert sub.status.value == 'ac'
            solved_task_ids.append(task.id)
            # sleep(random.uniform(0, 0.1))
        return solved_task_ids

    # 4) Run in parallel for two teams
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        fut_a = ex.submit(solve_tasks, client_a, N)
        fut_b = ex.submit(solve_tasks, client_b, N)
        ids_a = fut_a.result(timeout=20)
        ids_b = fut_b.result(timeout=20)

    print("Successfully solved tasks for Team A: ", len(ids_a))
    print("Successfully solved tasks for Team B: ", len(ids_b))

    # 5) Verify each team has exactly N AC tasks in the current round
    tasks_a_ac = client_a.list_tasks(status='ac').tasks
    tasks_b_ac = client_b.list_tasks(status='ac').tasks


    # For brand-new teams, AC count should match N exactly
    assert len(tasks_a_ac) == N
    assert len(tasks_b_ac) == N

    # Additionally, ensure no overlap of task IDs between teams (tasks are per-team)
    assert set(ids_a).isdisjoint(set(ids_b))







@pytest.mark.timeout(15)
def test_stress_claim_3workers() -> None:
    # three workers: Team A single worker; Team B two workers in parallel (may cause transaction conflicts)
    # Goal: Team A should not be impacted by Team B conflicts; everyone solves their quota.
    cache_dir = Path('.pytest_cache')
    cache_dir.mkdir(exist_ok=True)

    # Admin client
    admin_cfg = ConfigManager(cache_dir / 'stress_admin_3w.json')
    admin_client = ApiClient(admin_cfg)
    admin_client.save_api_key('admin1')

    from api_models import TeamsImportRequest, TeamCreateRequest

    req = TeamsImportRequest(
        challenge_id='challenge_1',
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
    b1_cfg = ConfigManager(cache_dir / 'stress3w_team_b1.json')
    b2_cfg = ConfigManager(cache_dir / 'stress3w_team_b2.json')

    client_a = ApiClient(a_cfg)
    client_a.save_api_key(teamA_key)
    client_b1 = ApiClient(b1_cfg)
    client_b1.save_api_key(teamB_key)
    client_b2 = ApiClient(b2_cfg)
    client_b2.save_api_key(teamB_key)

    N = 10  # per worker; total B will do 20 in total for Team B

    def solve_tasks_no_retry(client: ApiClient, n: int) -> list[str]:
        ids: list[str] = []
        for _ in range(n):
            task = client.claim_task(task_type='a_plus_b')
            # compute answer from input
            parts = (task.input or '').strip().split()
            a = int(parts[0]) if len(parts) > 0 else 0
            b = int(parts[1]) if len(parts) > 1 else 0
            ans = str(a + b)
            sub = client.submit_task_answer(SubmitAnswerRequest(task_id=task.id, answer=ans))
            assert sub.status.value == 'ac'
            ids.append(task.id)
        return ids

    def solve_tasks_with_retry(client: ApiClient, n: int, max_tries: int = 20) -> int:
        ids: list[str] = []
        attempts = 0
        while len(ids) < n:
            try:
                task = client.claim_task(task_type='a_plus_b')
            except Exception as e:
                attempts += 1
                if attempts > max_tries * n:
                    return attempts
                continue
            while True:
                try:
                    sub = client.submit_task_answer(SubmitAnswerRequest(task_id=task.id, answer="3"))
                    break
                except Exception as e:
                    attempts += 1
                    if attempts > max_tries * n:
                        return attempts
            assert sub.status.value == 'ac'
            ids.append(task.id)
        return attempts

    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        fut_b1 = ex.submit(solve_tasks_with_retry, client_b1, N//3, N//3)
        fut_b2 = ex.submit(solve_tasks_with_retry, client_b2, N//3, N//3)
        fut_b3 = ex.submit(solve_tasks_with_retry, client_b2, N//3, N//3)
        fut_a = ex.submit(solve_tasks_no_retry, client_a, N)
        ids_a = fut_a.result(timeout=30)
        duration = time.time() - start
        att1 = fut_b1.result(timeout=30)
        att2 = fut_b2.result(timeout=30)
        att3 = fut_b3.result(timeout=30)
        durationB = time.time() - start

    assert len(ids_a) == N
    print(f"Team A solved {N} tasks in {duration} seconds")
    print(f"Concurrent Team B worked in parallel and had {att1}, {att2} and {att3} retries because of conflicts, but still solved all tasks in {durationB} seconds")
    assert duration < 10
    # Validate Team A completeness and isolation
    tasks_a_ac = client_a.list_tasks(status='ac').tasks
    assert len(tasks_a_ac) == N
