import os
from datetime import datetime, timezone, timedelta

from api_models import TaskStatus
from back.firebase_db import get_firestore_db, FirebaseDatabase
from back.firebase_models import (
    ChallengeDocument, TeamDocument, APIKeyDocument, RoundDocument,
    TaskTypeDocument, TaskDocument
)


def setup_firebase_emulator() -> None:
    """Set up environment for Firebase emulator"""
    os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8080"
    os.environ["GOOGLE_CLOUD_PROJECT"] = "test-project"


def clear_firestore_data() -> None:
    """Clear all data from Firestore (emulator) with recursive subcollection cleanup"""
    db = get_firestore_db()
    
    # First, handle challenges with nested subcollections
    challenges_ref = db.collection('challenges')
    for ch_doc in challenges_ref.stream():
        ch_ref = challenges_ref.document(ch_doc.id)
        # Delete teams subcollection
        for team_doc in ch_ref.collection('teams').stream():
            team_doc.reference.delete()
        # Delete rounds and their nested subcollections (task_types, tasks, submissions)
        for rd_doc in ch_ref.collection('rounds').stream():
            rd_ref = ch_ref.collection('rounds').document(rd_doc.id)
            # Delete submissions under each task
            for t_doc in rd_ref.collection('tasks').stream():
                t_ref = rd_ref.collection('tasks').document(t_doc.id)
                for s_doc in t_ref.collection('submissions').stream():
                    s_doc.reference.delete()
                t_ref.delete()
            # Delete task types
            for tt_doc in rd_ref.collection('task_types').stream():
                tt_doc.reference.delete()
            rd_ref.delete()
        # Finally delete the challenge doc
        ch_ref.delete()
        print(f"Deleted document: {ch_doc.id}")
    
    # Then clear API keys
    keys_ref = db.collection('keys')
    for key_doc in keys_ref.stream():
        key_doc.reference.delete()
        print(f"Deleted document: {key_doc.id}")


def create_test_firebase_data() -> None:
    """Create test data in Firebase matching the SQL test data structure"""
    db = get_firestore_db()
    
    # Create challenges
    challenge1_id = "challenge_1"
    challenge2_id = "challenge_2"
    
    # Create teams (we will store them in subcollections)
    team1_id = "team_1"
    team2_id = "team_2"
    
    team1 = TeamDocument(
        id=team1_id,
        challenge_id=challenge1_id,
        name="Test Team 1",
        members="Member 1, Member 2",
        captain_contact="@xoposhiy"
    )
    
    team2 = TeamDocument(
        id=team2_id,
        challenge_id=challenge2_id,
        name="Test Team 2",
        members="Member 3, Member 4",
        captain_contact="@xoposhiy"
    )
    
    # Create rounds
    round1_id = "round_1"
    round2_id = "round_2"
    
    now = datetime.now(timezone.utc)
    
    # Prepare challenge docs (teams embedded map will be empty; teams are subcollection)
    challenge1 = ChallengeDocument(
        id=challenge1_id,
        title="Test Challenge 1",
        description="Description for test challenge 1",
        current_round_id=round1_id,
    )
    challenge2 = ChallengeDocument(
        id=challenge2_id,
        title="Test Challenge 2",
        description="Description for test challenge 2",
        current_round_id=round2_id,
    )
    
    # Store challenges first
    db.collection('challenges').document(challenge1_id).set(challenge1.model_dump())
    db.collection('challenges').document(challenge2_id).set(challenge2.model_dump())
    
    # Store teams as subcollection docs with deterministic IDs
    db.collection('challenges').document(challenge1_id).collection('teams').document(team1_id).set(team1.model_dump())
    db.collection('challenges').document(challenge2_id).collection('teams').document(team2_id).set(team2.model_dump())
    
    # Create round documents in subcollections with embedded task types
    task_type1 = TaskTypeDocument(
        type="a_plus_b",
        n_tasks=100,
        generator_url="http://127.0.0.1:8918/task_gen/a_plus_b",
        generator_settings="",
        generator_secret="twc",
        score=100,
        time_to_solve=30
    )
    task_type11 = TaskTypeDocument(
        type="sum_a_b",
        n_tasks=50,
        generator_url="http://127.0.0.1:8918/task_gen/a_plus_b",
        generator_settings="",
        generator_secret="twc",
        score=200,
        time_to_solve=30
    )
    task_type2 = TaskTypeDocument(
        type="test-type",
        n_tasks=5,
        generator_url="no-generator",
        generator_settings="",
        generator_secret="",
        score=100,
        time_to_solve=45
    )

    round1 = RoundDocument(
        id=round1_id,
        challenge_id=challenge1_id,
        published=True,
        claim_by_type=True,
        start_time=now,
        end_time=now + timedelta(hours=2000),
        task_types=[task_type1, task_type11]
    )
    round2 = RoundDocument(
        id=round2_id,
        challenge_id=challenge2_id,
        published=False,
        claim_by_type=False,
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=2000),
        task_types=[task_type2]
    )

    challenge1_rounds = db.collection('challenges').document(challenge1_id).collection('rounds')
    challenge1_rounds.document(round1_id).set(round1.model_dump())

    challenge2_rounds = db.collection('challenges').document(challenge2_id).collection('rounds')
    challenge2_rounds.document(round2_id).set(round2.model_dump())

    # Create tasks and store inside round1 document (as field)
    tasks = {
        "task_1": TaskDocument(
            id="task_1",
            challenge_id=challenge1_id,
            team_id=team1_id,
            round_id=round1_id,
            type="a_plus_b",
            status=TaskStatus.PENDING,
            statement="Given two integers a and b, find their sum a + b.",
            input="1 2",
            checker_hint="",
            score=100,
            claimed_at=now
        ).model_dump(),
        "task_2": TaskDocument(
            id="task_2",
            challenge_id=challenge1_id,
            team_id=team1_id,
            round_id=round1_id,
            type="sum_a_b",
            status=TaskStatus.PENDING,
            statement="You can't solve this task. It has no generator",
            input="This is some strange task input",
            checker_hint="",
            score=0,
            claimed_at=now - timedelta(minutes=5)
        ).model_dump(),
        "task_3": TaskDocument(
            id="task_3",
            challenge_id=challenge1_id,
            team_id=team1_id,
            round_id=round1_id,
            type="test-type",
            status=TaskStatus.AC,
            statement="You can't solve this task. It has no generator",
            input="This is some strange task input",
            checker_hint="",
            score=200,
            claimed_at=now - timedelta(minutes=10)
        ).model_dump(),
        "task_4": TaskDocument(
            id="task_4",
            challenge_id=challenge1_id,
            team_id=team1_id,
            round_id=round1_id,
            type="test-type",
            status=TaskStatus.WA,
            statement="You can't solve this task. It has no generator",
            input="This is some strange task input",
            checker_hint="",
            score=0,
            claimed_at=now - timedelta(minutes=20)
        ).model_dump()
    }
    # Store tasks as subcollection documents under the round
    r1_tasks_ref = challenge1_rounds.document(round1_id).collection('tasks')
    for tid, tdoc in tasks.items():
        r1_tasks_ref.document(tid).set(tdoc)
    
    # Create API keys
    api_keys = [
        APIKeyDocument(
            key="admin1",
            challenge_id=challenge1_id,
            role="admin",
            team_id=None
        ),
        APIKeyDocument(
            key="admin2",
            challenge_id=challenge2_id,
            role="admin",
            team_id=None
        ),
        APIKeyDocument(
            key="team1",
            challenge_id=challenge1_id,
            role="player",
            team_id=team1_id
        ),
        APIKeyDocument(
            key="team2",
            challenge_id=challenge2_id,
            role="player",
            team_id=team2_id
        )
    ]
    
    for api_key in api_keys:
        db.collection('keys').document(api_key.key).set(api_key.model_dump())
    
    print("Firebase test data created successfully!")


def is_firebase_connection_ok() -> bool:
    """Test Firebase connection and basic operations"""
    db = get_firestore_db()

    # Test write
    test_doc = {"test": "data", "timestamp": datetime.now()}
    db.collection('test').document('connection_test').set(test_doc)
    print("[OK] Write test passed")

    # Test read
    doc = db.collection('test').document('connection_test').get()
    if doc.exists:
        print("[OK] Read test passed")
        print(f"  Data: {doc.to_dict()}")
    else:
        print("[FAIL] Read test failed - document not found")

    # Cleanup
    db.collection('test').document('connection_test').delete()
    print("[OK] Delete test passed")
    return True


if __name__ == "__main__":
    setup_firebase_emulator()
    FirebaseDatabase.reset_connection()  # Reset to use emulator
    
    print("Clearing existing data...")
    clear_firestore_data()

    print("Creating test data...")
    create_test_firebase_data()
    print("Firebase emulator setup complete!")