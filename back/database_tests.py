import unittest
from database import get_test_db_session

from models_orm import Challenge, Task, Base

class TestDatabase(unittest.TestCase):
    """Test cases for database functionality"""

    def setUp(self):
        # Use the in-memory SQLite database for testing
        self.db = get_test_db_session(create_tables=True)

    def tearDown(self):
        """Clean up after each test"""
        self.db.close()


    def test_create_challenge(self):
        """Test creating a challenge in the database"""
        # Create a new challenge
        challenge = Challenge(title="Test Challenge")
        self.db.add(challenge)
        self.db.commit()
        
        # Query the challenge
        db_challenge = self.db.query(Challenge).filter(Challenge.title == "Test Challenge").first()
        
        # Assert that the challenge was created correctly
        self.assertIsNotNone(db_challenge)
        self.assertEqual(db_challenge.title, "Test Challenge")


    def test_create_task(self):
        """Test creating a task in the database"""
        # Create a new task
        task = Task(title="Test Task", status="PENDING")
        self.db.add(task)
        self.db.commit()
        
        # Query the task
        db_task = self.db.query(Task).filter(Task.title == "Test Task").first()
        
        # Assert that the task was created correctly
        self.assertIsNotNone(db_task)
        self.assertEqual(db_task.title, "Test Task")
        self.assertEqual(db_task.status, "PENDING")

    def test_update_challenge(self):
        """Test updating a challenge in the database"""
        # Create a new challenge
        challenge = Challenge(title="Original Title")
        self.db.add(challenge)
        self.db.commit()
        
        # Update the challenge
        challenge.title = "Updated Title"
        self.db.commit()
        
        # Query the challenge
        db_challenge = self.db.query(Challenge).filter(Challenge.id == challenge.id).first()
        
        # Assert that the challenge was updated correctly
        self.assertEqual(db_challenge.title, "Updated Title")

    def test_delete_challenge(self):
        """Test deleting a challenge from the database"""
        # Create a new challenge
        challenge = Challenge(title="To Be Deleted")
        self.db.add(challenge)
        self.db.commit()
        
        # Get the challenge ID
        challenge_id = challenge.id
        
        # Delete the challenge
        self.db.delete(challenge)
        self.db.commit()
        
        # Try to query the deleted challenge
        db_challenge = self.db.query(Challenge).filter(Challenge.id == challenge_id).first()
        
        # Assert that the challenge was deleted
        self.assertIsNone(db_challenge)

if __name__ == "__main__":
    unittest.main()