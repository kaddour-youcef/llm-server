# Repository Guidelines

## Project Structure & Module Organization
- Source: place code under `src/` (e.g., `src/main` or `src/app`).
- Tests: keep in `tests/` mirroring `src/` paths (e.g., `tests/test_main.py` or `tests/app.spec.ts`).
- Scripts & Ops: use `scripts/` for maintenance tasks; put runtime configs in `configs/` and sample env in `.env.example`.
- Docs & Assets: add developer notes to `docs/`; keep Docker/compose files in `docker/`.

## Build, Test, and Development Commands
- Make (recommended): define standard targets `make dev`, `make run`, `make build`, `make test`, `make lint`, `make fmt`, `make clean`.
  - Example: `make dev` (starts hot-reload server), `make test` (runs unit tests), `make lint` (static analysis), `make fmt` (auto-format).
- Containers: `docker compose up --build` to run locally with dependencies.
- Language runners: if applicable, expose `npm run dev` / `npm test` (Node) or `uvicorn src.app:app --reload` / `pytest -q` (Python) via `make` for a single entry point.

## Coding Style & Naming Conventions
- Formatting: enforce via tooling and CI. Prefer `make fmt` to run formatters.
- Indentation: 4 spaces for Python; 2 spaces for JS/TS. Line length 100–120 chars.
- Naming: `snake_case` for Python modules/files; `camelCase` for variables/functions; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants. Keep directories lowercase with hyphens.

## Testing Guidelines
- Location: all tests in `tests/` with names like `test_*.py` (Python) or `*.spec.ts`/`*.test.ts` (JS/TS).
- Coverage: target ≥80% line coverage for changed code.
- Commands: `make test` for the default test suite; use `make test P=<pattern>` (or framework flags) to filter.

## Commit & Pull Request Guidelines
- Commits: follow Conventional Commits, e.g., `feat(api): add chat route`, `fix(auth): handle token refresh`.
- Scope: small, focused commits with clear intent; reference issues like `#123`.
- PRs: include a summary, motivation, screenshots or logs (when useful), test evidence, and any config/docs updates. Ensure CI is green.

## Security & Configuration Tips
- Secrets: never commit real `.env` files; commit `.env.example` only.
- Least privilege: scope keys/tokens narrowly; rotate regularly.
- Local safety: add logs/redactions that avoid leaking prompts or credentials in debug output.
