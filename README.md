# odin-l2-workflow

A Python project (AWS CDK app) for managing and deploying AWS related infrastructure for processing Odin Level 2 data.


## Installation

### Prerequisites
- Python 3.13 or higher
- Node.js 22 (for AWS CDK)
- [uv](https://docs.astral.sh/uv/) package manager

### Setup Steps

1. **Clone the repository:**
	 ```bash
	 git clone https://github.com/Odin-SMR/odin-l2-workflow.git
	 cd odin-l2-workflow
	 ```

2. **Install Node.js 22 (if not already installed):**
	 ```bash
	 # Using nvm (recommended)
	 nvm install 22
	 nvm use 22
	 
	 # Or use the version specified in .nvmrc
	 nvm use
	 ```

3. **Install AWS CDK CLI:**
	 ```bash
	 npm install -g aws-cdk
	 ```

4. **Set up Python dependencies:**
	 ```bash
	 uv sync --locked --all-groups
	 ```

## Usage

### Development Commands
- **Run linters:**
    ```bash
    # Check code formatting with Black
    uv run black --check .
    
    # Check code style with Ruff
    uv run ruff check .
    ```

- **Run type checks:**
    ```bash
    uv run mypy .
    ```

- **Run tests:**
	```bash
	uv run pytest
	```

### AWS CDK Deployment
- **Synthesize CDK stacks:**
	```bash
	cdk synth --profile your-aws-profile
	```

- **Deploy CDK stacks:**
	```bash
	cdk deploy --profile your-aws-profile
	```

### Development
- **Develop Lambda handlers:**
	Edit or add files in `level2/handlers/`.

## Contributing
1. Clone the repository and create your branch.
2. Make your changes and add tests as needed.
3. Run `pytest` to ensure all tests pass.
4. Submit a pull request with a clear description of your changes.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For questions or support, please open an issue on the [GitHub repository](https://github.com/Odin-SMR/odin-l2-workflow).
