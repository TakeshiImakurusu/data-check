# Repository Guidelines

## Project Structure & Module Organization
- `data_check.py` hosts the Tkinter desktop app, wiring progress tracking, menu actions, and series-level checks.
- Series logic lives in `dekispart.py`, `innosite.py`, `dekispart_school.py`, and `cloud.py`; each exposes `fetch_data`, `validate_data`, and `save_to_excel` helpers consumed by the UI.
- Persistent configuration is stored in `app_settings.json` (auxiliary file paths) and `check_definitions.json` (per-check metadata). Adjust these locally; do not commit secrets.
- Sample source data, CSVs, and spreadsheets stay in `input_file/`; treat them as fixtures when validating logic.
- Architectural and requirement references are captured in `design.md`, `requirements.md`, and the Japanese spec `データチェックシステム_チェック定義設計書.md`.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` creates an isolated environment; install `pandas`, `pymysql`, `pyodbc`, `openpyxl`, and other connectors there.
- `python data_check.py` launches the GUI against the configured databases.
- `python -m compileall .` offers a quick syntax pass before packaging; run it prior to release builds.

## Coding Style & Naming Conventions
- Follow PEP 8: four-space indentation, lowercase_with_underscores for functions, and CapWords for classes (e.g., `DataCheckerApp`).
- Prefer descriptive constants (`APP_VERSION`, `contract_fields`) and reuse shared validation helpers to avoid duplicated business rules.
- Keep UI strings and SQL queries close to their series module unless shared across series; factor common widgets into dedicated builders if reuse grows.

## Testing Guidelines
- Add unit tests with `pytest` or `unittest` for each series module, mocking database calls via fixtures; target critical branches in `validate_data`.
- Store golden CSV/XLSX samples under `input_file/tests/` to isolate from production fixtures.
- Exercise the GUI end-to-end at least once per release, capturing screenshots of filters, exports, and error dialogs for QA notes.

## Commit & Pull Request Guidelines
- Use present-tense, imperative commit subjects (`Add school-series cross-check`); include Japanese context if it clarifies business rules.
- Reference related tickets or document updates in the body, and call out schema/config changes explicitly.
- Pull requests should summarize impacted series, list manual or automated test evidence, and attach screenshots for GUI-visible changes.

## Security & Configuration Tips
- Never commit real credentials: replace them with environment variables or a local `config.ini` ignored by Git.
- When sharing logs or error exports, redact user identifiers and regenerate from sanitized fixtures.
