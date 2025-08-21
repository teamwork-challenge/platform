import os
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore as gcs_firestore
from typing import Optional


class FirebaseDatabase:
    _db: Optional[gcs_firestore.Client] = None
    _app: Optional[firebase_admin.App] = None
    
    @classmethod
    def get_db(cls) -> gcs_firestore.Client:
        """
        Returns Firestore client.
        Uses emulator if FIRESTORE_EMULATOR_HOST is set, otherwise uses production.
        """
        if cls._db is not None:
            return cls._db
        
        # Check if we're using the emulator
        emulator_host = os.environ.get("FIRESTORE_EMULATOR_HOST")
        
        if emulator_host:
            print(f"Using Firestore emulator at {emulator_host}")
            # For emulator, we don't need credentials
            os.environ["GOOGLE_CLOUD_PROJECT"] = "twchallenge-24d46"
            cls._db = gcs_firestore.Client(project="twchallenge-24d46") # type: ignore[arg-type]
        else:
            print("Using Firestore production")
            # Initialize Firebase Admin SDK for production
            if cls._app is None:
                cred = credentials.ApplicationDefault()
                cls._app = firebase_admin.initialize_app(cred)
            cls._db = firestore.client()
        
        return cls._db
    
    @classmethod
    def reset_connection(cls) -> None:
        """Reset the database connection (useful for tests)"""
        cls._db = None
        if cls._app:
            firebase_admin.delete_app(cls._app)
            cls._app = None


def get_firestore_db() -> gcs_firestore.Client:
    """Convenience function to get Firestore database instance"""
    return FirebaseDatabase.get_db()