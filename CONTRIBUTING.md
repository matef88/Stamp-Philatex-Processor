# 🤝 Contributing to Stamp Philatex Processor

Thank you for your interest in contributing! This document provides guidelines for contributions.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

---

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Publishing others' private information
- Other unprofessional conduct

---

## How to Contribute

### Ways to Contribute

1. **Report Bugs** - Open an issue with details
2. **Suggest Features** - Share your ideas
3. **Improve Documentation** - Fix typos, add examples
4. **Submit Code** - Fix bugs, add features
5. **Review Pull Requests** - Help review changes

### Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/matef88/Stamp-Philatex-Processor.git
   ```
3. Create a branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Development Setup

### Prerequisites

- Python 3.9 - 3.11
- Git
- Conda or venv

### Setup Steps

```bash
# Create environment
conda create -n stamp_dev python=3.11
conda activate stamp_dev

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest black flake8

# Run tests
python -m pytest tests/

# Run application
python run_gui.py
```

### Project Structure

```
stamp-philatex-processor/
├── gui/                # PyQt6 GUI code
├── scripts/            # Core processing scripts
├── docs/               # Documentation
├── tests/              # Test files
├── config.yaml         # Configuration
└── run_gui.py          # Entry point
```

---

## Pull Request Process

### Before Submitting

1. **Test your changes**
   ```bash
   python -m pytest tests/
   ```

2. **Format your code**
   ```bash
   black .
   ```

3. **Check for issues**
   ```bash
   flake8 .
   ```

4. **Update documentation** if needed

5. **Update CHANGELOG.md** with your changes

### Submitting

1. Push to your fork
2. Open a Pull Request
3. Fill in the PR template
4. Wait for review

### PR Requirements

- [ ] Code compiles without errors
- [ ] Tests pass
- [ ] Code is formatted with Black
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG.md updated
- [ ] PR description is clear

---

## Coding Standards

### Python Style

- Follow PEP 8
- Use Black formatter
- Maximum line length: 100 characters
- Use type hints where appropriate

### Example

```python
from typing import List, Optional


def process_stamps(
    image_paths: List[str],
    output_dir: str,
    confidence: float = 0.5,
) -> Optional[List[str]]:
    """
    Process a list of stamp images.
    
    Args:
        image_paths: List of paths to images
        output_dir: Directory for output files
        confidence: Detection confidence threshold
    
    Returns:
        List of output file paths, or None on failure
    """
    # Implementation here
    pass
```

### Documentation

- Use docstrings for all public functions/classes
- Keep comments up-to-date
- Document complex logic

### Commits

- Write clear commit messages
- Reference issues when applicable
- Keep commits focused

**Good commit messages:**
```
Add batch processing progress bar
Fix alignment issue for rotated stamps
Update documentation for GPU setup
```

**Bad commit messages:**
```
Fixed stuff
Updated code
Changes
```

---

## Reporting Bugs

### Before Reporting

1. Check existing issues
2. Try the latest version
3. Check documentation

### Bug Report Template

```markdown
**Description**
A clear description of the bug.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment**
- OS: [e.g., Windows 11]
- Python version: [e.g., 3.11]
- GPU: [e.g., NVIDIA RTX 3060]

**Additional Context**
Any other relevant information.
```

---

## Feature Requests

### Before Requesting

1. Check existing feature requests
2. Consider if it fits the project scope

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Any alternative solutions you've considered.

**Additional context**
Any other context or screenshots about the feature.
```

---

## Development Tips

### Running Tests

```bash
# All tests
python -m pytest

# Specific test file
python -m pytest tests/test_processing.py

# With coverage
python -m pytest --cov=scripts tests/
```

### Debugging

Enable debug logging:
```yaml
# config.yaml
logging:
  level: "DEBUG"
```

### GUI Development

Test theme changes:
```bash
python run_gui.py --theme light
python run_gui.py --theme dark
```

---

## Questions?

- Open a Discussion on GitHub
- Check existing documentation
- Review closed issues

---

Thank you for contributing! 🎉

*Last updated: December 2024*
