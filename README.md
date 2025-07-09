# Teamwork Challenge Platform

A comprehensive platform for hosting programming teamwork challenges designed to help freshman CS and SE students learn teamwork by doing.

## Overview

The Teamwork Challenge Platform is designed to create an intensive, game-like programming experience that immerses students in real collaboration. The platform hosts challenges that run in 4-hour rounds, feeling like mini-hackathons, where teams must distribute tasks, collaborate using Git, handle uncertainty, and mitigate technical risks.

### Key Features

- **Round-based Challenges**: Challenges run in 4-hour rounds that feel like mini-hackathons
- **Task Distribution**: Each round contains several task types, encouraging teams to split work
- **Dynamic Task Generation**: Tasks are generated on the fly, nudging students to automate repeated steps
- **Intentional Incompleteness**: Task statements are intentionally incomplete to encourage experimentation and knowledge sharing
- **Integration Requirements**: Later tasks require integrating earlier solutions, reinforcing Git workflow
- **Structured Retrospectives**: Teams analyze and improve their process after every round

## Components

The platform consists of several components:

1. **Backend API**: A FastAPI-based REST API that manages challenges, rounds, teams, tasks, and submissions
2. **Command Line Interface**: A Python-based CLI for interacting with the platform
3. **Task Generators**: REST APIs that generate tasks and validate solutions

## Documentation

For more detailed information, see the documentation in the `/docs` directory:

- [Vision & Goals](/docs/1-Vision.md): Project vision and goals
- [Specification](/docs/2-Specification.md): Detailed specifications
- [Backend](/docs/3-Backend.md): Backend API details
- [CLI](/docs/4-CLI.md): Command Line Interface details
- [Task Generators](/docs/5-TaskGenerators.md): Task generator API details

## Component-Specific Documentation

- [Backend README](/back/README.md): Backend setup and usage
- [CLI README](/cli/README.md): CLI setup and usage
- [Tasks README](/tasks/README.md): Task generator information

## Setting Up Python Dev Environment

- Install Python 3.11
- Setup PyCharm: 
	- File → Settings → Project → Python Interpreter
	- If no virtual env is not yet set — create it:
		- Add Local
		- Generate New, Virtualenv, Python 3.11.
	- Rename interpreter to "Python 3.11" to match commited `./idea/platform.iml`.

