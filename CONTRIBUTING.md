# Contributing to Shift Agent

Thank you for your interest in contributing to the Shift Agent project! This guide will help you get started.

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (required for Timefold compatibility)
- **Java 17** (required for Timefold Solver)
- **uv** package manager
- **Git**

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/shiftagent.git
   cd shiftagent
   ```

2. **Set up development environment**
   ```bash
   make setup
   ```

3. **Verify installation**
   ```bash
   make test
   make run
   ```

4. **Access the application**
   - API: http://localhost:8081
   - Documentation: http://localhost:8081/docs

## 📋 Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes
Follow our coding standards (see below) and ensure your changes:
- Have appropriate tests
- Follow the existing code style
- Include documentation updates if needed

### 3. Test Your Changes
```bash
# Run all tests
make test

# Test API endpoints
make test-api

# Check code quality
make lint
make format
```

### 4. Commit Your Changes
```bash
git add .
git commit -m "feat: add new scheduling constraint"
```

**Commit Message Format:**
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation updates
- `test:` - Test improvements
- `refactor:` - Code refactoring
- `perf:` - Performance improvements

### 5. Submit a Pull Request
```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear description of changes
- Reference to any related issues
- Screenshots for UI changes
- Test results

## 🏗️ Project Architecture

### Directory Structure
```
src/shiftagent/
├── api/              # FastAPI application layer
│   ├── routes.py     # API endpoints
│   ├── schemas.py    # Request/response models
│   ├── solver.py     # Timefold solver config
│   └── jobs.py       # Async job management
├── core/             # Domain logic
│   ├── models/       # Domain models (Employee, Shift, Schedule)
│   └── constraints/  # Optimization constraints
├── mcp/              # MCP server for AI assistants
└── utils/            # Utilities and demo data
```

### Key Components
- **Domain Models**: Employee, Shift, ShiftSchedule with Timefold annotations
- **Constraints**: Optimization rules (skills, hours, fairness)
- **API Layer**: FastAPI endpoints with async job processing
- **MCP Server**: AI assistant integration

## 🎯 Contribution Areas

### High Priority
- **New Constraints**: Add scheduling rules (seniority, availability)
- **Performance**: Optimize solver configuration
- **API Features**: New endpoints for schedule management
- **Documentation**: API examples and tutorials

### Medium Priority
- **UI Components**: Frontend for schedule visualization
- **Integrations**: Calendar systems, HR software
- **Monitoring**: Metrics and logging improvements
- **Testing**: Integration and performance tests

### Getting Started Issues
Look for issues labeled:
- `good first issue` - Simple, well-defined tasks
- `help wanted` - Areas where we need assistance
- `documentation` - Docs improvements

## 🧪 Testing Guidelines

### Test Types
1. **Unit Tests** (`tests/test_*.py`)
   - Test individual functions and classes
   - Mock external dependencies
   ```bash
   uv run pytest tests/test_models.py -v
   ```

2. **API Tests** (`api-test.http`)
   - Test HTTP endpoints
   - Validate request/response formats
   ```bash
   make test-api
   ```

3. **Integration Tests**
   - Test complete workflows
   - Verify solver integration

### Writing Tests
```python
def test_employee_skills_validation():
    """Test that employee skills are properly validated."""
    employee = Employee(
        id="emp1",
        name="Test Employee",
        skills={"python", "api"}
    )
    assert "python" in employee.skills
    assert len(employee.skills) == 2
```

## 📝 Code Style Guidelines

### Python Standards
- **Formatter**: ruff (line length: 88)
- **Import sorting**: ruff (built-in)
- **Type hints**: Required for new code
- **Docstrings**: Google style for public functions

### Code Quality Checks
```bash
# Format code
make format

# Check linting
make lint

# Type checking
uv run mypy src/
```

### Naming Conventions
- **Classes**: PascalCase (`ShiftSchedule`)
- **Functions/Variables**: snake_case (`get_employee_shifts`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_WEEKLY_HOURS`)
- **Files**: snake_case (`shift_constraints.py`)

## 🐛 Bug Reports

### Before Reporting
1. Search existing issues
2. Test with latest version
3. Check troubleshooting guide

### Bug Report Template
```markdown
**Bug Description**
Clear description of the issue

**Steps to Reproduce**
1. Step one
2. Step two
3. Expected vs actual behavior

**Environment**
- Python version: 3.11.x
- Operating system: macOS/Linux/Windows
- Browser (if applicable): Chrome/Safari/Firefox

**Logs/Screenshots**
Include relevant error messages
```

## 💡 Feature Requests

### Feature Request Template
```markdown
**Feature Description**
What feature would you like to see?

**Use Case**
Why is this feature important?

**Proposed Solution**
How should this feature work?

**Alternatives**
Any alternative approaches considered?
```

## 🔧 Development Commands

| Command | Description |
|---------|-------------|
| `make setup` | Complete development setup |
| `make run` | Start FastAPI server |
| `make run-mcp` | Start API + MCP servers |
| `make test` | Run all tests |
| `make format` | Format code with ruff |
| `make lint` | Run linters (ruff, mypy) |
| `make clean` | Clean cache and artifacts |
| `make debug` | Start server in debug mode |

## 📚 Resources

### Documentation
- [Timefold Solver Docs](https://docs.timefold.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Project API Docs](http://localhost:8081/docs) (when running)

### Learning Materials
- [Constraint Optimization](https://docs.timefold.ai/timefold-solver/latest/quickstart/quickstart)
- [Employee Scheduling Guide](https://docs.timefold.ai/timefold-solver/latest/use-cases-and-examples/employee-rostering/employee-rostering)

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Focus on the technical merits

### Getting Help
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Questions and general discussion
- **Documentation**: Check CLAUDE.md for development guidance

## ⚖️ License

By contributing, you agree that your contributions will be licensed under the Apache-2.0 License.

---

Thank you for contributing to Shift Agent! 🙏

For questions about contributing, please open a GitHub issue or discussion.
