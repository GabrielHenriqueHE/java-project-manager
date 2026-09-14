# Feature 03 — Gerenciamento de Módulos — Tasks

Fase 1 entregou apenas os **stubs** da interface (`add_module`/`remove_module`/`update_dependency`/`update_metadata` levantando `NotImplementedError`).

**`remove_module` implementado** na Fase 2 (`specs/phases/phase-2-remover-modulo/`): funcional de ponta a ponta no `MavenAdapter` (com detecção de dependentes via `DependentModuleConflict`) e na TUI (`ProjectDetailScreen`, binding `r` + `ConfirmModal`).

Ainda como stub (`NotImplementedError`): `add_module`, `update_dependency`, `update_metadata` — ficam para fatias seguintes da Fase 2.
