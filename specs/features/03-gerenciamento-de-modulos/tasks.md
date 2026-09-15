# Feature 03 — Gerenciamento de Módulos — Tasks

Fase 1 entregou apenas os **stubs** da interface (`add_module`/`remove_module`/`update_dependency`/`update_metadata` levantando `NotImplementedError`).

**`remove_module` implementado** na Fase 2 (`specs/phases/phase-2-remover-modulo/`): funcional de ponta a ponta no `MavenAdapter` (com detecção de dependentes via `DependentModuleConflict`) e na TUI (`ProjectDetailScreen`, binding `r` + `ConfirmModal`).

**`add_module` implementado** na Fase 2 (`specs/phases/phase-2-add-module/`): funcional de ponta a ponta no `MavenAdapter` (cria diretório/pom/estrutura padrão, registra no pai, herda groupId/version quando aplicável) e na TUI (`ProjectDetailScreen`, binding `a` + `ModuleFormScreen`).

**`update_metadata` implementado** na Fase 2 (`specs/phases/phase-2-update-metadata/`): funcional de ponta a ponta no `MavenAdapter` (herança de groupId/version, artifactId somente-leitura, packaging protegido em módulos com submódulos/BOM) e na TUI (Painel [2] METADADOS, binding `enter` + `MetadataFormScreen`).

Ainda como stub (`NotImplementedError`): `update_dependency` — fica para a fatia seguinte da Fase 2.
