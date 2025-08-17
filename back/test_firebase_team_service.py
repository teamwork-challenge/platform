import pytest

from api_models import TeamCreateRequest, UserRole
from firebase_db import FirebaseDatabase
from firebase_team_service import TeamService
from firebase_test_setup import setup_firebase_emulator, clear_firestore_data, create_test_firebase_data


class TestFirebaseTeamService:
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
        self.service = TeamService()
    
    def test_get_auth_data_admin_key(self):
        """Test getting auth data for admin API key"""
        auth_data = self.service.get_auth_data("admin1")
        
        assert auth_data is not None
        assert auth_data.key == "admin1"
        assert auth_data.role == UserRole.ADMIN
        assert auth_data.team_id is None
        assert auth_data.challenge_id is None
    
    def test_get_auth_data_team_key(self):
        """Test getting auth data for team API key"""
        auth_data = self.service.get_auth_data("team1")
        
        assert auth_data is not None
        assert auth_data.key == "team1"
        assert auth_data.role == UserRole.PLAYER
        assert auth_data.team_id is not None
        assert auth_data.challenge_id is not None
        # Should have current round ID if round is published
        assert auth_data.round_id is not None
    
    def test_get_auth_data_invalid_key(self):
        """Test getting auth data for invalid API key"""
        auth_data = self.service.get_auth_data("invalid_key")
        assert auth_data is None
    
    def test_get_teams_by_challenge(self):
        """Test getting all teams for a specific challenge"""
        teams = self.service.get_teams_by_challenge("challenge_1")
        
        assert len(teams) == 1
        team = teams[0]
        assert team.name == "Test Team 1"
        assert team.members == "Member 1, Member 2"
        assert team.captain_contact == "@xoposhiy"
        assert team.api_key == ""  # Should not expose API key
    
    def test_get_teams_by_invalid_challenge(self):
        """Test getting teams for non-existent challenge"""
        teams = self.service.get_teams_by_challenge("invalid_challenge")
        assert len(teams) == 0
    
    def test_get_all_teams(self):
        """Test getting all teams across all challenges"""
        teams = self.service.get_all_teams()
        
        assert len(teams) == 2  # Test data has 2 teams across 2 challenges
        team_names = [team.name for team in teams]
        assert "Test Team 1" in team_names
        assert "Test Team 2" in team_names
    
    def test_create_teams(self):
        """Test creating new teams"""
        new_teams = [
            TeamCreateRequest(
                name="New Team 1",
                members="Alice, Bob",
                captain_contact="alice@example.com"
            ),
            TeamCreateRequest(
                name="New Team 2", 
                members="Charlie, David",
                captain_contact="charlie@example.com"
            )
        ]
        
        created_teams = self.service.create_teams("challenge_1", new_teams)
        
        assert len(created_teams) == 2
        
        # Verify teams were created with API keys
        for team in created_teams:
            assert team.api_key is not None
            assert len(team.api_key) > 0
        
        # Verify teams can be retrieved
        all_teams = self.service.get_teams_by_challenge("challenge_1")
        assert len(all_teams) == 3  # 1 existing + 2 new teams
        
        # Verify API keys were created and work for auth
        for team in created_teams:
            auth_data = self.service.get_auth_data(team.api_key)
            assert auth_data is not None
            assert auth_data.role == UserRole.PLAYER
    
    def test_create_teams_invalid_challenge(self):
        """Test creating teams for non-existent challenge"""
        new_teams = [
            TeamCreateRequest(
                name="Test Team",
                members="Test Member",
                captain_contact="test@example.com"
            )
        ]
        
        with pytest.raises(ValueError):
            self.service.create_teams("invalid_challenge_id", new_teams)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])