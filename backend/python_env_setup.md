# Python Virtual Environment Setup

## Initial Setup (one-time)

Create the virtual environment:
```bash
python3 -m venv venv
```

Activate the virtual environment:
```bash
source venv/bin/activate
```

Install project dependencies:
```bash
pip install -r requirements.txt
```

Install the project in editable mode (makes `src` importable):
```bash
pip install -e .
```

## Daily Usage

Every time you start working on the project, activate the virtual environment:
```bash
source venv/bin/activate
```

You'll know it's activated when you see `(venv)` in your terminal prompt.

## Running Tests

With the virtual environment activated:
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agents/test_goal_generator.py -v

# Run with verbose output and print statements
pytest -v -s
```

## Deactivating

When you're done working:
```bash
deactivate
```

## Notes

- The `venv/` folder is like `node_modules/` in JavaScript - it's excluded from git
- Always activate the virtual environment before running any Python code or tests
- If you add new dependencies, update `requirements.txt` and run `pip install -r requirements.txt` again