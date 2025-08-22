from unittest.mock import patch
from typing import Any

import pytest

from api_models import GenResponse, CheckResponse, CheckResult, CheckStatus, TaskStatus
from back.services.db import FirebaseDatabase
from back.services.task_service import FirebaseTaskService
from back.tests.test_setup import setup_firebase_emulator, clear_firestore_data, create_test_firebase_data


class TestFirebaseTaskService:
    @classmethod
    def setup_class(cls) -> None:
        """Set up Firebase emulator for all tests"""
        setup_firebase_emulator()
        FirebaseDatabase.reset_connection()
    
    @classmethod
    def teardown_class(cls) -> None:
        """Clean up after all tests"""
        clear_firestore_data()
        FirebaseDatabase.reset_connection()
    
    def setup_method(self) -> None:
        """Set up each test method"""
        clear_firestore_data()
        create_test_firebase_data()
        self.service = FirebaseTaskService()
    
    def test_list_tasks_for_team(self) -> None:
        """Test listing tasks for a team"""
        tasks = self.service.list_tasks_for_team("team_1", "challenge_1", round_id="round_1")
        
        assert len(tasks) == 4  # Test data has 5 tasks for team_1
        
        # Check that tasks are ordered by claimed_at descending
        for i in range(len(tasks) - 1):
            assert tasks[i].claimed_at >= tasks[i + 1].claimed_at
        
        # Test filtering by status
        pending_tasks = self.service.list_tasks_for_team("team_1", "challenge_1", status=TaskStatus.PENDING, round_id="round_1")
        assert len(pending_tasks) > 0  # 2 PENDING tasks in test data
        
        ac_tasks = self.service.list_tasks_for_team("team_1", "challenge_1", status=TaskStatus.AC, round_id="round_1")
        assert len(ac_tasks) == 1  # 1 AC task in test data
    
    def test_list_tasks_for_invalid_team(self) -> None:
        """Test listing tasks for non-existent team"""
        tasks = self.service.list_tasks_for_team("invalid_team", "challenge_1", round_id="round_1")
        assert len(tasks) == 0
    
    def test_get_task(self) -> None:
        """Test getting a specific task"""
        # We know from test data that task_1 exists
        task = self.service.get_task("task_1", "challenge_1", "round_1")
        
        assert task is not None
        assert task.status == TaskStatus.PENDING
        assert "Given two integers a and b, find their sum a + b." in task.statement
    
    def test_get_task_invalid(self) -> None:
        """Test getting non-existent task"""
        task = self.service.get_task("invalid_task", "challenge_1", "round_1")
        assert task is None
    
    @patch('back.services.task_service.TaskGenClient.generate_task')
    def test_create_task(self, mock_generate_task: Any) -> None:
        """Test creating a new task"""
        # Mock the task generator response
        mock_gen_response = GenResponse(
            statement="Test generated statement",
            input="test input",
            checker_hint="test hint",
            statement_version="1.0"
        )
        mock_generate_task.return_value = mock_gen_response
        
        # Create a new task
        new_task = self.service.create_task("challenge_1", "round_1", "team_1", "a_plus_b")
        
        assert new_task is not None
        assert new_task.status == TaskStatus.PENDING
        assert new_task.statement == "Test generated statement"
        assert new_task.input == "test input"
        assert "a_plus_b" in new_task.type

        # Verify the generator was called
        mock_generate_task.assert_called_once()
        
        # Verify the task was added to the database
        tasks = self.service.list_tasks_for_team("team_1", "challenge_1", round_id="round_1")
        assert len(tasks) > 4  # 4 existing + 1 new
    
    def test_create_task_invalid_challenge(self) -> None:
        """Test creating task for non-existent challenge"""
        with pytest.raises(ValueError, match="Challenge not found"):
            self.service.create_task("invalid_challenge", "round_1", "team_1", "a_plus_b")
    
    def test_create_task_invalid_task_type(self) -> None:
        """Test creating task with invalid task type"""
        with pytest.raises(ValueError, match="No task type found"):
            self.service.create_task("challenge_1", "round_1", "team_1", "invalid_type")

    @patch('back.services.task_service.TaskGenClient.check_answer')
    def test_submit_task_answer_accepted(self, mock_check_answer: Any) -> None:
        """Test submitting a correct answer"""
        # Mock the checker response
        mock_check_result = CheckResult(
            status=CheckStatus.ACCEPTED,
            score=1.0,
            error="",
            collaborative_scores=[]
        )
        mock_check_response = CheckResponse([mock_check_result])
        mock_check_answer.return_value = mock_check_response
        
        # Submit answer for task_1 (which is PENDING)
        submission = self.service.submit_task_answer("task_1", "team_1", "challenge_1", "round_1", "3")
        
        assert submission is not None
        assert submission.status.value == "ac"
        assert submission.answer == "3"
        assert submission.score == 100  # Full score from test data
        
        # Verify the checker was called
        mock_check_answer.assert_called_once()
        
        # Verify task status was updated
        updated_task = self.service.get_task("task_1", "challenge_1", "round_1")
        assert updated_task is not None
        assert updated_task.status == TaskStatus.AC
    
    @patch('back.services.task_service.TaskGenClient.check_answer')
    def test_submit_task_answer_wrong_answer(self, mock_check_answer: Any) -> None:
        """Test submitting a wrong answer"""
        # Mock the checker response
        mock_check_result = CheckResult(
            status=CheckStatus.WRONG_ANSWER,
            score=0.0,
            error="Wrong answer",
            collaborative_scores=[]
        )
        mock_check_response = CheckResponse([mock_check_result])
        mock_check_answer.return_value = mock_check_response
        
        # Submit wrong answer for task_2 (which is PENDING)
        submission = self.service.submit_task_answer("task_2", "team_1", "challenge_1", "round_1", "wrong")
        
        assert submission is not None
        assert submission.status.value == "wa"
        assert submission.answer == "wrong"
        assert submission.score == 0
        assert "Wrong answer" in submission.checker_output
        
        # Verify task status was updated
        updated_task = self.service.get_task("task_2", "challenge_1", "round_1")
        assert updated_task is not None
        assert updated_task.status == TaskStatus.WA
    
    def test_submit_task_answer_invalid_task(self) -> None:
        """Test submitting answer for non-existent task"""
        with pytest.raises(ValueError, match="Task not found"):
            self.service.submit_task_answer("invalid_task", "team_1", "challenge_1", "round_1", "answer")
    
    def test_submit_task_answer_wrong_team(self) -> None:
        """Test submitting answer for task that doesn't belong to team"""
        with pytest.raises(ValueError, match="Task does not belong to this team"):
            self.service.submit_task_answer("task_1", "team_2", "challenge_1", "round_1", "answer")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])