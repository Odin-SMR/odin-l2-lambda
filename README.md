# odin-l2-workflow

A Python project (AWS CDK app) for managing and deploying AWS related infrastructure for processing Odin Level 2 data.


## Installation
1. **Clone the repository:**
	 ```bash
	 git clone https://github.com/Odin-SMR/odin-l2-workflow.git
	 cd odin-l2-workflow
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
1. Clone the repository and create your branch.
2. Make your changes and add tests as needed.
3. Run `pytest` to ensure all tests pass.
4. Submit a pull request with a clear description of your changes.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For questions or support, please open an issue on the [GitHub repository](https://github.com/Odin-SMR/odin-l2-workflow).
