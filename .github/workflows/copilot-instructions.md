# Project Overview

This is a cdk-based Python app for the Odin SMR Level 2 data for managing level 2 data processing. Currently it puts messages on SQS queues to trigger batch processing Lambda functions in a ECR stack.

# Project aims

Provide a cost-effective and scalable solution for processing Level 2 data using AWS services.

# Coding guidelines

- Follow codstyle enforced by `black` and `ruff`.
- Use type hints and validate with `mypy`.
- Write unit tests using `pytest`.

For detailed setup and development instructions, please refer to our [Development Guide](../README.md).
