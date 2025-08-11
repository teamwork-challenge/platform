# Teamwork Challenge Platform: Backend API

## Overview

The Backend API is a core component of the Teamwork Challenge Platform, providing RESTful endpoints for managing challenges, rounds, teams, tasks, and submissions. It serves as the central hub for all platform interactions, enabling both administrative functions and player activities.

## Architecture

The backend is built with FastAPI, a modern, high-performance web framework for building APIs with Python. The architecture follows a layered approach:

- **API Layer**: Handles HTTP requests and responses
- **Service Layer**: Implements business logic
- **Alchemy ORM** as data layer

## Installation

1. Install the dependencies to be able to build and run the API:
   ```bash
   back> pip install -r requirements-dev.txt
   ```
2. Install AWS CLI. https://aws.amazon.com/cli/
3. Ask AWS admin for Access Key Name, Access Key Secret and Region Name. Use them to configure AWS CLI:
   ```bash
   back> aws configure
   ```
4. By this command you can check the AWS access Key name, access Key secret and Region name:
   ```bash
   back> aws sts get-caller-identity
   ```
5. Run test in database_aws_tests.py to check the connection to the could database.

## Deployment

1. Install AWS SAM CLI. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
2. `back> sam build` to build the application (in `back\` directory).
3. `back> sam deploy` to deploy the application.

Public deployment: https://93a6a2ehkb.execute-api.eu-north-1.amazonaws.com/docs


## Running the API locally

In the root directory:

   ```bash
   platform> python -m back.main
   ```
## Type checking

In the root directory:

   ```bash
   platform> mypy back
   ```

Once running, you can access:
- API at: `http://localhost:8000`
- Swagger UI documentation at: `http://localhost:8000/docs`
- ReDoc documentation at: `http://localhost:8000/redoc`

## More details

See [Backend Documentation](../docs/2-Backend.md) in the docs directory.
