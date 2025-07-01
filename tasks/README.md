# Teamwork Challenge: Sample Public Task Generators

The Fast-API application that hosts task generators for the Teamwork Challenge platform.

Endpoints:
```
/{generator}/statements
/{generator}/gen
/{generator}/check
```

## Architecture

Use router to define endpoints for each task generator.

Use separate folder for each task generator.

To adapt fast api for the AWS lambda, use `Mangum` to wrap the FastAPI app.

Secret Keys are stored in the Secrets Manager, and are accessed using the `boto3` library.

## Requirements

Task Generator API models are defined in shared module api_modules, the same way as it does `back` project.

- requirements-base.txt contains the common parts of the next two files.
- requirements-dev.txt contains the dependencies needed to run the task generator API. Adds api_modules as editable dependency.
- requirements.txt contains the dependencies needed to run the task generator API in production.


template.yaml defines the AWS Lambda function and its API Gateway configuration (the same as in `back` project).