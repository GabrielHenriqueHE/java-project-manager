# Feature 02 — Metadados do Projeto — Tasks

Coberto parcialmente pela **Fase 1** (modelo `ProjectMetadata` + visualização somente-leitura) — ver `specs/phases/phase-1-fundacao/tasks.md` (tasks T4, T7, T8, T12).

**Edição de metadados implementada** na Fase 2 (`specs/phases/phase-2-update-metadata/`): `update_metadata` funcional de ponta a ponta no `MavenAdapter` (com herança de groupId/version do pai e proteção de artifactId somente-leitura) e na TUI (`MetadataPanel`, binding `enter` + `MetadataFormScreen`).
