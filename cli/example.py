#!/usr/bin/env python3
"""
Example script demonstrating how to use the Teamwork Challenge CLI.

This script shows how to:
1. Login to the challenge platform
2. View team information
3. Claim a task
4. Submit an answer
5. View the leaderboard

Run this script with:
    python example.py
"""

import subprocess
import sys
import time

def run_command(command):
    """Run a CLI command and print the output."""
    print(f"\n> {command}")
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result

def main():
    print("Checking if the CLI is available...")
    result = run_command("python cli\\main.py --help")
    if result.returncode != 0:
        print("Error: CLI not found. Make sure you're in the project root directory.")
        sys.exit(1)

    print("\nStep 1: Login with your API key")
    run_command("python cli\\main.py login sample_api_key_123")

    print("\nStep 2: View your team information")
    run_command("python cli\\main.py team show")

    print("\nStep 3: View available rounds")
    run_command("python cli\\main.py round list")

    print("\nStep 4: Claim a task")
    run_command("python cli\\main.py task claim --type math")

    print("\nStep 5: List your tasks")
    run_command("python cli\\main.py task list")

    print("\nStep 6: Submit an answer for a task")
    run_command("python cli\\main.py task submit task123 \"42\"")

    print("\nStep 7: View the leaderboard")
    run_command("python cli\\main.py board leaderboard")

    print("\nStep 8: Logout")
    run_command("python cli\\main.py logout")
    
    print("\nExample completed successfully!")

if __name__ == "__main__":
    main()