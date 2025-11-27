# Test System Rebirth: A Guide to Running Tests

The project's test infrastructure has been rebuilt from the ground up to be stable, reliable, and easy to use.

## 1. Running Tests Locally

### Prerequisites

1.  **Install Python Dependencies**: Ensure all required packages are installed from `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```
2.  **No Database Needed**: The test suite is configured to use a self-contained, in-memory SQLite database. No external database setup is required.

### Executing the Test Suite

To run the entire test suite, execute the following command from the root of the project:

```bash
python -m pytest
```

To run a specific test file:

```bash
python -m pytest tests/smoke/test_api_smoke.py
```

## 2. CI/CD Test Execution

The test suite is automatically executed on every push and pull request to the `main` branch via the workflow defined in `.github/workflows/ci.yml`.

The CI pipeline performs the following key steps:
1.  Installs Python and Node.js dependencies (with caching).
2.  Builds the frontend application (`npm run build`).
3.  Performs linting and format checks with `ruff`.
4.  Performs static type checking with `mypy`.
5.  Executes the full `pytest` suite.

A passing CI check is a mandatory requirement for merging any code.

## 3. Test Philosophy & Architecture

*   **Isolation**: Tests are fully isolated. The database is wiped clean after every test, and the application is configured with a temporary file system for static assets.
*   **Fixtures**: Core functionality (like the application instance, database sessions, and test clients) is provided via fixtures in `tests/conftest.py`.
*   **Speed**: By using an in-memory database and avoiding external network calls (via mocking), the test suite is designed to run quickly and efficiently.
*   **Reliability**: The rebuilt test kernel eliminates the flakiness and configuration errors that previously plagued the system.
