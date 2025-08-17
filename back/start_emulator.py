#!/usr/bin/env python3
"""
Simple script to run Firebase tests with manual emulator setup instructions
"""
import subprocess
import sys

from back.firebase_db import FirebaseDatabase
from back.firebase_test_setup import setup_firebase_emulator, is_firebase_connection_ok, create_test_firebase_data, \
    clear_firestore_data


def run_tests() -> bool:
    """Run Firebase tests assuming emulator is running"""
    print("Setting up Firebase emulator environment...")
    setup_firebase_emulator()
    FirebaseDatabase.reset_connection()
    
    print("Testing Firebase connection...")
    if is_firebase_connection_ok():
        print("Connection test successful!")
        
        print("\nClearing any existing data...")
        clear_firestore_data()
        
        print("Creating test data...")
        create_test_firebase_data()
        
        print("Running pytest tests...")
        try:
            result = subprocess.run([sys.executable, "-m", "pytest", "test_firebase.py", "test_firebase_team_service.py", "-v"], 
                                  capture_output=True, text=True)
            print("STDOUT:")
            print(result.stdout)
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            
            if result.returncode == 0:
                print("All tests passed!")
                return True
            else:
                print("Some tests failed.")
                return False
        except Exception as e:
            print(f"Error running pytest: {e}")
            return False
    else:
        print("Connection test failed!")
        return False


def print_manual_emulator_instructions() -> None:
    """Print instructions for starting the emulator manually"""
    print("=" * 60)
    print("FIREBASE EMULATOR SETUP INSTRUCTIONS")
    print("=" * 60)
    print()
    print("To start the Firebase Firestore emulator manually:")
    print()
    print("1. Install Firebase CLI (if not already installed):")
    print("   npm install -g firebase-tools")
    print()
    print("2. Start the emulator in a separate terminal:")
    print("   firebase emulators:start --only firestore")
    print("   OR")
    print("   firebase emulators:start --only firestore --port 8080")
    print()
    print("3. The emulator should start on localhost:8080")
    print("   You can access the UI at: http://localhost:4000")
    print()
    print("4. Once the emulator is running, run this script again:")
    print(f"   python {__file__}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print_manual_emulator_instructions()
        sys.exit(0)
    
    print("Firebase Test Runner")
    print("===================")
    
    success = run_tests()
    
    if not success:
        print("\nIf the emulator is not running, please start it manually:")
        print_manual_emulator_instructions()
        sys.exit(1)
    else:
        print("\n[SUCCESS] All Firebase tests completed successfully!")
        sys.exit(0)