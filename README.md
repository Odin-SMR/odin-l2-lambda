# odin-l2-lambda

A Python project for managing and deploying AWS Lambda functions and related infrastructure using AWS CDK. This repository is part of the Odin-SMR and is designed to facilitate batch processing and ECR (Elastic Container Registry) stack management for Level 2 data workflows.

## Features
- AWS Lambda function deployment and management
- Batch processing handlers
- Infrastructure as code using AWS CDK
- Modular codebase for easy extension
- Automated testing with pytest

## Project Structure
```
odin-l2-lambda/
├── app.py                  # CDK application entry point
├── cdk.json                # CDK configuration
├── level2/                 # Core Python package
│   ├── handlers/           # Lambda and batch handlers
│   └── requirements.txt    # Python dependencies for Lambda
├── stacks/                 # CDK stack definitions
├── tests/                  # Unit tests
├── pyproject.toml          # Project metadata and dependencies
├── req.txt                 # Additional requirements
└── README.md               # Project documentation
```

## Installation
1. **Clone the repository:**
	 ```bash
	 git clone https://github.com/Odin-SMR/odin-l2-lambda.git
	 cd odin-l2-lambda
	 ```
2. **Set up a Python virtual environment:**
	 ```bash
        uv sync --all-groups
	 ```

## Usage
- **Deploy CDK stacks:**
	```bash
    cdk synth --profile your-aws-profile
	cdk deploy --profile your-aws-profile
	```

- **Run linter:**
    ```bash
    uv run black --check .
    ```

- **Run mypy type checks:**
    ```bash
    uv run mypy .
    ```
- **Run tests:**
	```bash
	uv run pytest
	```
- **Develop Lambda handlers:**
	Edit or add files in `level2/handlers/`.

## Contributing
1. Fork the repository and create your branch.
2. Make your changes and add tests as needed.
3. Run `pytest` to ensure all tests pass.
4. Submit a pull request with a clear description of your changes.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For questions or support, please open an issue on the [GitHub repository](https://github.com/Odin-SMR/odin-l2-lambda).
