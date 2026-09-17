# AGENTS.md

This file provides guidance to AI Agents when working with code in this repository.

## What this is

`jpm` (Java Project Manager) is a **Python/Textual TUI** — not a Java tool. It manages the structure of Java projects (Maven today, Gradle planned) from the outside: creating/removing modules, editing metadata, keeping the parent POM, BOM (`dependencyManagement`) and dependent modules in sync. The project itself is Python; "Java" refers to what it manages.

Full product context, glossary, and the architectural decision log live in `specs/00-overview.md` — read it before making structural changes. Development follows a lightweight, custom Spec-Driven Development flow documented there (`specs/features/`, `specs/phases/`); `specs/phases/<phase>/tasks.md` is the source of truth for what's actually done.

## Workflow

Work directly on the main checkout — **no need to create a git worktree to make code changes in this repo**. There's a single active line of work here, and a worktree only adds isolation overhead this project doesn't need. Edit files in place, run the tests, and commit on `main` (or whatever branch is already checked out) when asked to. (`.claude/settings.json` sets `worktree.bgIsolation: "none"` so background sessions aren't forced into a worktree either.)

## Commands

```bash
uv sync                                          # install deps (Python 3.13+, uv required)
uv run jpm                                       # run the app
uv run textual run --dev src/manager/app.py      # run with Textual dev console (for `textual console`)
uv run pytest                                    # run all tests
uv run pytest tests/test_main_screen.py -k name  # run a single test
uv run black src tests                           # format
uv run isort src tests                           # sort imports
```

Tests use `pytest-asyncio` in `auto` mode (see `pyproject.toml`) — async test functions don't need an explicit marker.

## Architecture

**Domain model is build-tool agnostic; adapters translate to/from real build files.**

- `src/manager/models.py` — Pydantic models (`Project`, `Module`, `Dependency`, `ProjectMetadata`, `DirectoryStructure`, ...). This is the vocabulary every other layer speaks.
- `src/manager/adapters/base.py` — `BuildToolAdapter` ABC every build tool implements: `detect`, `infer_structure`, `add_module`, `remove_module`, `update_dependency`, `update_metadata`, `add_directory`, `remove_directory`, `remove_dependency`, `register_directory_role`. All ten are implemented end-to-end in `MavenAdapter`.
- `src/manager/adapters/maven/` — the only implementation today (`adapter.py` orchestrates, `parser.py` reads POMs, `writer.py` edits them, `directory.py` handles module scaffolding on disk, `xml_utils.py` for namespace/XPath helpers). Uses `lxml` specifically to preserve formatting/comments in the user's POM and minimize diffs.
- `src/manager/services/adapters_registry.py` — `detect_adapter(path)` picks the right `BuildToolAdapter` for a project root. Add new build tools here.
- `src/manager/services/registry.py` — `ProjectRegistry`, the **only** persistent state owned by the app itself (`~/.config/java-project-manager/registry.json`: known project paths + build tool). Everything else about a project's structure is never persisted — it's always re-derived live via `infer_structure()` to avoid drift from the real files on disk (e.g. after a `git pull` or manual edit).
- `src/manager/screens/main_screen.py` + `src/manager/screens/widgets/` — the TUI itself.

**Key rule when touching adapters:** never invent a source of truth for project structure — it must come from re-reading the build files. The registry only stores *which* projects exist and *which* adapter to use, never their contents.

### TUI layout

Single-screen, 3-column, 5-panel layout ("mvnforge"), replacing an earlier multi-screen flow (Dashboard → Import → ProjectDetail) that was deliberately discarded — don't reintroduce separate screens for this. Full spec: `specs/design/tui-layout.md`.

- Col 1: `[1] PROJETOS` over `[3] MÓDULOS`
- Col 2: `[2] METADADOS` over `[4] BOM + DEPENDÊNCIAS`
- Col 3: `[5] ESTRUTURA` (full column)
- `1`-`5`/`tab` switch panel focus, `j`/`k` move within a list (or the Estrutura checklist), `n` create, `d` delete, `enter` select/edit (or create the highlighted directory in Estrutura), `b` register the active directory in the build (Estrutura), `space` toggle active module in Estrutura, `:` opens command mode (e.g. `:modulo <nome>`).

`MainScreen` owns shared state (`project`, `selected_module`) and propagates refresh to panels after mutations.

Known Textual gotchas hit in this codebase (see `specs/phases/phase-3-redesign-tui/tasks.md` notes):
- `Panel.focus_default()` on the base widget only calls `self.focus()`, which is a no-op for panels with `can_focus = False` (the `ListView`-backed ones). Those panels must override `focus_default()` to delegate to the inner `ListView`.
- A binding declared on `Panel.BINDINGS` isn't auto-applied to a focused child widget (e.g. `ListView`) — panels implement `action_cursor_down`/`action_cursor_up` themselves and delegate explicitly.
- Rebuilding a list in a refresh method (e.g. `ProjectsPanel.refresh_projects`) must restore `list_view.index` afterward, or the selection resets and breaks whatever shortcut runs next (e.g. `d`).
