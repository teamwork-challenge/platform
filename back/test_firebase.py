import pytest
import os
from datetime import datetime, timezone
from firebase_db import FirebaseDatabase, get_firestore_db
from firebase_test_setup import setup_firebase_emulator, clear_firestore_data, create_test_firebase_data
from firebase_models import ChallengeDocument, TeamDocument, APIKeyDocument


class TestFirebaseSetup:
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
    
    def test_firebase_connection(self):
        """Test basic Firebase connection and CRUD operations"""
        db = get_firestore_db()
        
        # Test write
        test_data = {
            "test_field": "test_value",
            "timestamp": datetime.now(timezone.utc)
        }
        doc_ref = db.collection('test_collection').document('test_doc')
        doc_ref.set(test_data)
        
        # Test read
        doc = doc_ref.get()
        assert doc.exists
        data = doc.to_dict()
        assert data['test_field'] == 'test_value'
        
        # Test update
        doc_ref.update({"test_field": "updated_value"})
        updated_doc = doc_ref.get()
        assert updated_doc.to_dict()['test_field'] == 'updated_value'
        
        # Test delete
        doc_ref.delete()
        deleted_doc = doc_ref.get()
        assert not deleted_doc.exists
    
    def test_create_test_data(self):
        """Test creation of test data structure"""
        create_test_firebase_data()
        
        db = get_firestore_db()
        
        # Verify challenges exist
        challenge1 = db.collection('challenges').document('challenge_1').get()
        assert challenge1.exists
        
        challenge_data = challenge1.to_dict()
        assert challenge_data['title'] == 'Test Challenge 1'
        # Teams are now a subcollection. Verify a team doc exists.
        team1 = db.collection('challenges').document('challenge_1').collection('teams').document('team_1').get()
        assert team1.exists
        
        # Verify rounds exist as subcollection
        round1 = db.collection('challenges').document('challenge_1').collection('rounds').document('round_1').get()
        assert round1.exists
        
        # Verify API keys exist
        admin_key = db.collection('keys').document('admin1').get()
        assert admin_key.exists
        
        key_data = admin_key.to_dict()
        assert key_data['role'] == 'admin'
        assert key_data['challenge_id'] == 'challenge_1'
        
        team_key = db.collection('keys').document('team1').get()
        assert team_key.exists
        
        team_key_data = team_key.to_dict()
        assert team_key_data['role'] == 'player'
        assert team_key_data['team_id'] == 'team_1'
    

    def test_api_key_lookup(self):
        """Test API key document structure for auth lookups"""
        create_test_firebase_data()
        
        db = get_firestore_db()
        
        # Test admin key lookup
        admin_key_doc = db.collection('keys').document('admin1').get()
        admin_data = admin_key_doc.to_dict()
        
        assert admin_data['key'] == 'admin1'
        assert admin_data['role'] == 'admin'
        assert admin_data['challenge_id'] == 'challenge_1'
        assert admin_data['team_id'] is None
        
        # Test team key lookup
        team_key_doc = db.collection('keys').document('team1').get()
        team_data = team_key_doc.to_dict()
        
        assert team_data['key'] == 'team1'
        assert team_data['role'] == 'player'
        assert team_data['challenge_id'] == 'challenge_1'
        assert team_data['team_id'] == 'team_1'


if __name__ == "__main__":
    pytest.main([__file__])