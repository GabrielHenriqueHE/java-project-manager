# Feature 03 — Gerenciamento de Módulos — Tasks

Fase 1 entregou apenas os **stubs** da interface (`add_module`/`remove_module`/`update_dependency`/`update_metadata` levantando `NotImplementedError`).

**`remove_module` implementado** na Fase 2 (`specs/phases/phase-2-remover-modulo/`): funcional de ponta a ponta no `MavenAdapter` (com detecção de dependentes via `DependentModuleConflict`) e na TUI (`ProjectDetailScreen`, binding `r` + `ConfirmModal`).

**`add_module` implementado** na Fase 2 (`specs/phases/phase-2-add-module/`): funcional de ponta a ponta no `MavenAdapter` (cria diretório/pom/estrutura padrão, registra no pai, herda groupId/version quando aplicável) e na TUI (`ProjectDetailScreen`, binding `a` + `ModuleFormScreen`).

**`update_metadata` implementado** na Fase 2 (`specs/phases/phase-2-update-metadata/`): funcional de ponta a ponta no `MavenAdapter` (herança de groupId/version, artifactId somente-leitura, packaging protegido em módulos com submódulos/BOM) e na TUI (Painel [2] METADADOS, binding `enter` + `MetadataFormScreen`).

**`update_dependency` implementado** na Fase 2 (`specs/phases/phase-2-update-dependency/`): funcional de ponta a ponta no `MavenAdapter` (upsert de dependências gerenciadas/diretas por `groupId:artifactId`) e na TUI (Painel [4] BOM + DEPENDÊNCIAS, binding `n` + `DependencyFormScreen`, sempre gerenciada/BOM no módulo selecionado no Painel [3]).

Todas as mutações previstas para a Fase 2 (`add_module`, `remove_module`, `update_metadata`, `update_dependency`) estão implementadas.

**`remove_dependency` implementado** na Fase 5 (`specs/phases/phase-5-remover-dependencia/`): novo método na interface `BuildToolAdapter`, remove uma dependência gerenciada (BOM) identificada por `groupId:artifactId` em qualquer módulo que a declare, reaproveitando o `MavenPomWriter.remove_managed_dependency` já existente desde a Fase 2. TUI: Painel [4], binding `d`.

Ainda fora de escopo: adicionar/editar dependência **direta** (`managed=False`) de um módulo qualquer pela TUI — sem painel para isso no layout atual.
