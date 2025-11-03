# Contributing Guide

This guide explains how to set up, code, test, review, and release updates so that all contributions meet our team’s **Definition of Done (DoD)** and maintain consistent quality across the project.


## Code of Conduct

All contributors should behave in a respectful, professional, and inclusive manner. Please follow the [Contributor Covenant](https://www.contributor-covenant.org/) code of conduct. Harassment or discrimination of any kind will not be tolerated. If you experience or witness inappropriate behavior, please report it to the project manager or through official OSU channels. 

## Getting Started

### **Prerequisites**

* Python 3.11+
* Git and GitHub account
* Access to the project repository and required API keys (stored in `.env`, not committed to Git)

### **Setup**

```bash
git clone https://github.com/rrithik/Natural-Language-Processing-of-Financial-Disclosures.git
cd Natural-Language-Processing-of-Financial-Disclosures
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

To run the app locally:

```bash
python main.py
```

Environment variables (e.g., API keys) must be placed in a `.env` file and **never committed** to Git.


## Branching & Workflow

We use a **feature-branch workflow** based on the `main` branch.

**Naming convention:**

```
feature/<short-description>
bugfix/<issue-id>
docs/<update-description>
```

* Create a new branch for each task or issue.
* Rebase frequently to stay updated with `main`.
* Merge via Pull Request (PR) after at least one approved review.


## Issues & Planning

* File new issues under the **Issues** tab with the correct label (e.g., `bug`, `enhancement`, `documentation`).
* Use the provided issue template.
* The project manager assigns issues during weekly sprint planning.
* Include an estimated completion time and relevant links if applicable.


## Commit Messages

Follow the **Conventional Commits** standard:

```
<type>(scope): short description
```

**Examples:**

```
feat(parser): add SEC 8-K file processing logic
fix(ci): correct lint-check job syntax
docs(readme): update setup instructions
```

Each commit should reference an issue number when applicable, e.g., `#12`.


## Code Style, Linting & Formatting

We use **Black**, **Flake8**, and **isort** for code formatting and linting.

**Config files:**

* `.flake8`
* `pyproject.toml`

**Commands:**

```bash
black .
isort .
flake8 .
mypy .
```

These checks also run automatically through CI before merging any PR.
0


## Testing

* All new features and bug fixes must include **unit or integration tests** in the `/tests` directory.
* Run all tests locally before pushing:

  ```bash
  pytest -v
  ```
* A PR cannot be merged if any test fails in CI.
* Minimum coverage target: **75%**.


## Pull Requests & Reviews

Before opening a PR:

1. Run `black .`, `flake8 .`, and `pytest -v`.
2. Ensure your branch is rebased on the latest `main`.
3. Fill out the PR template, describing your changes and testing.
4. Request review from at least one teammate.

PRs must:

* Pass all CI checks
* Receive **≥ 1 approval**
* Be small and focused (under ~400 lines of diff preferred)


## CI/CD

* CI pipeline file: [`.github/workflows/linter-check.yml`](https://github.com/rrithik/Natural-Language-Processing-of-Financial-Disclosures/blob/main/.github/workflows/linter-check.yml)
* Linting and tests run automatically on every push and pull request.
* You can view logs or re-run jobs from the [GitHub Actions Dashboard](https://github.com/rrithik/Natural-Language-Processing-of-Financial-Disclosures/actions).
* All required checks must pass before merging to `main`.


## Security & Secrets

* Never commit API keys, credentials, or `.env` files.
* Report security concerns privately to the team lead or instructor.
* Use `.gitignore` to exclude sensitive files.
* Dependencies are updated monthly using Dependabot or manual review.


## Documentation Expectations

* Update relevant docs for every feature or fix:

  * `README.md`
  * `/docs/` folder
  * Inline code comments and docstrings
* Follow Python’s **PEP 257** docstring conventions.
* Update the changelog after significant releases.


## Release Process

* Use **semantic versioning** (`v1.2.0`, `v1.2.1`, etc.).
* Tag releases via GitHub after successful CI runs.
* Update the changelog (`CHANGELOG.md`) for every release.
* If a rollback is required, revert the corresponding release tag and issue a hotfix branch.


## Support & Contact

 For general questions: open a **Discussion** or contact the project manager via Discord or email.
* Response time: within **24 hours** during weekdays.
* Maintainers:

  * Norman O’Brien (Documentation Lead / Head of Architecture / Tester)
  * Rithik Nibbara (Head of testing / Developer)
  * Hsun-Yu Kuo (Meeting Coordinator / Developer)
  * Trinity Paulson (Project Manager)
