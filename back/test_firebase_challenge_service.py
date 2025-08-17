from datetime import datetime, timezone, timedelta

import pytest

from api_models import ChallengeUpdateRequest, RoundCreateRequest, RoundTaskTypeCreateRequest
from firebase_challenge_service import ChallengeService
from firebase_db import FirebaseDatabase
from firebase_test_setup import setup_firebase_emulator, clear_firestore_data, create_test_firebase_data


class TestFirebaseChallengeService:
    @classmethod
    def setup_class(cls):
        """Set up Firebase emulator for all tests"""
        setup_firebase_emulator()
        FirebaseDatabase.reset_connection()
    
    @classmethod
    def teardown_class(cls):
        """Clean up after all tests"""
        clear_firestore_data()
        FirebaseDatabase.reset_connection()
    
    def setup_method(self):
        """Set up each test method"""
        clear_firestore_data()
        create_test_firebase_data()
        self.service = ChallengeService()
    
    def test_get_challenge(self):
        """Test getting a challenge by ID"""
        challenge = self.service.get_challenge("challenge_1")
        
        assert challenge is not None
        assert challenge.title == "Test Challenge 1"
        assert challenge.description == "Description for test challenge 1"
        assert challenge.current_round_id is not None  # Should have published round
    
    def test_get_challenge_invalid(self):
        """Test getting non-existent challenge"""
        challenge = self.service.get_challenge("invalid_challenge")
        assert challenge is None
    
    def test_get_all_challenges(self):
        """Test getting all challenges"""
        challenges = self.service.get_all_challenges()
        
        assert len(challenges) == 2
        challenge_titles = [c.title for c in challenges]
        assert "Test Challenge 1" in challenge_titles
        assert "Test Challenge 2" in challenge_titles
    
    def test_create_challenge(self):
        """Test creating a new challenge"""
        new_challenge = self.service.create_challenge(
            title="New Test Challenge",
            description="A brand new test challenge"
        )
        
        assert new_challenge is not None
        assert new_challenge.title == "New Test Challenge"
        assert new_challenge.description == "A brand new test challenge"
        assert new_challenge.current_round_id is None  # No rounds yet
        
        # Verify it was actually created
        all_challenges = self.service.get_all_challenges()
        assert len(all_challenges) == 3  # 2 existing + 1 new
    
    def test_update_challenge(self):
        """Test updating a challenge"""
        update_data = ChallengeUpdateRequest(
            title="Updated Challenge Title",
            description="Updated description"
        )
        
        updated_challenge = self.service.update_challenge("challenge_1", update_data)
        
        assert updated_challenge is not None
        assert updated_challenge.title == "Updated Challenge Title"
        assert updated_challenge.description == "Updated description"
        
        # Verify the update persisted
        retrieved_challenge = self.service.get_challenge("challenge_1")
        assert retrieved_challenge.title == "Updated Challenge Title"
    
    def test_update_challenge_invalid(self):
        """Test updating non-existent challenge"""
        update_data = ChallengeUpdateRequest(title="New Title")
        result = self.service.update_challenge("invalid_challenge", update_data)
        assert result is None
    
    def test_get_rounds_by_challenge(self):
        """Test getting rounds for a challenge"""
        rounds = self.service.get_rounds_by_challenge("challenge_2")
        
        assert len(rounds) == 1
        round = rounds[0]
        assert round.claim_by_type is True
        assert round.published is False
    
    def test_get_rounds_by_invalid_challenge(self):
        """Test getting rounds for non-existent challenge"""
        rounds = self.service.get_rounds_by_challenge("invalid_challenge")
        assert len(rounds) == 0
    
    def test_create_round(self):
        """Test creating a new round"""
        now = datetime.now(timezone.utc)
        round_data = RoundCreateRequest(
            challenge_id="challenge_1",
            start_time=now,
            end_time=now + timedelta(hours=24),
            claim_by_type=True,
        )
        
        new_round = self.service.create_round(round_data)
        
        assert new_round is not None
        assert new_round.challenge_id == "challenge_1"
        assert new_round.claim_by_type is True
        assert new_round.published is False
        
        # Verify it was added to the challenge
        rounds = self.service.get_rounds_by_challenge("challenge_1")
        assert new_round.id in [r.id for r in rounds]
    
    def test_create_round_task_type(self):
        """Test creating a round task type"""
        task_type_data = RoundTaskTypeCreateRequest(
            round_id="round_1",
            type="new_task_type",
            generator_url="http://example.com/generator",
            generator_settings="{}",
            generator_secret="secret123",
            max_tasks_per_team=50,
            score=200,
            time_to_solve=60
        )
        
        new_task_type = self.service.create_round_task_type(task_type_data, "challenge_1")
        
        assert new_task_type is not None
        assert new_task_type.type == "new_task_type"
        assert new_task_type.generator_url == "http://example.com/generator"
        assert new_task_type.score == 200
        assert new_task_type.time_to_solve == 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])