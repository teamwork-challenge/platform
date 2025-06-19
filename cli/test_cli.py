#!/usr/bin/env python3
"""
Test script for the Teamwork Challenge CLI.

This script tests the basic functionality of the CLI by importing it
and calling its functions directly, rather than through the command line.

Run this script with:
    python test_cli.py
"""

import sys
from io import StringIO
from contextlib import redirect_stdout

# Import the CLI app
from main import app, login, whoami, team_show, round_list, task_claim, task_list, board_leaderboard

def test_function(func, *args, **kwargs):
    """Test a CLI function by capturing its output."""
    print(f"\n=== Testing {func.__name__} ===")
    
    # Capture stdout
    f = StringIO()
    with redirect_stdout(f):
        try:
            # Call the function with the provided arguments
            if args or kwargs:
                func(*args, **kwargs)
            else:
                func()
            result = "Success"
        except Exception as e:
            result = f"Error: {str(e)}"
    
    # Get the captured output
    output = f.getvalue()
    
    print(f"Result: {result}")
    if output:
        print("Output:")
        print(output)

def main():
    print("Testing Teamwork Challenge CLI...")
    
    # Test login
    test_function(login, "test_api_key")
    
    # Test whoami
    test_function(whoami)
    
    # Test team show
    test_function(team_show)
    
    # Test round list
    test_function(round_list)
    
    # Test task claim
    test_function(task_claim, task_type="math")
    
    # Test task list
    test_function(task_list)
    
    # Test board leaderboard
    test_function(board_leaderboard)
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main()