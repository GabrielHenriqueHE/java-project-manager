# Feature 03 — Gerenciamento de Módulos — Tasks

Fase 1 entregou apenas os **stubs** da interface (`add_module`/`remove_module`/`update_dependency`/`update_metadata` levantando `NotImplementedError`).

**`remove_module` implementado** na Fase 2 (`specs/phases/phase-2-remover-modulo/`): funcional de ponta a ponta no `MavenAdapter` (com detecção de dependentes via `DependentModuleConflict`) e na TUI (`ProjectDetailScreen`, binding `r` + `ConfirmModal`).

**`add_module` implementado** na Fase 2 (`specs/phases/phase-2-add-module/`): funcional de ponta a ponta no `MavenAdapter` (cria diretório/pom/estrutura padrão, registra no pai, herda groupId/version quando aplicável) e na TUI (`ProjectDetailScreen`, binding `a` + `ModuleFormScreen`).

**`update_metadata` implementado** na Fase 2 (`specs/phases/phase-2-update-metadata/`): funcional de ponta a ponta no `MavenAdapter` (herança de groupId/version, artifactId somente-leitura, packaging protegido em módulos com submódulos/BOM) e na TUI (Painel [2] METADADOS, binding `enter` + `MetadataFormScreen`).

**`update_dependency` implementado** na Fase 2 (`specs/phases/phase-2-update-dependency/`): funcional de ponta a ponta no `MavenAdapter` (upsert de dependências gerenciadas/diretas por `groupId:artifactId`) e na TUI (Painel [4] BOM + DEPENDÊNCIAS, binding `n` + `DependencyFormScreen`, sempre gerenciada/BOM no módulo selecionado no Painel [3]).

Todas as mutações previstas para a Fase 2 (`add_module`, `remove_module`, `update_metadata`, `update_dependency`) estão implementadas.

**`remove_dependency` implementado** na Fase 5 (`specs/phases/phase-5-remover-dependencia/`): novo método na interface `BuildToolAdapter`, remove uma dependência gerenciada (BOM) identificada por `groupId:artifactId` em qualquer módulo que a declare, reaproveitando o `MavenPomWriter.remove_managed_dependency` já existente desde a Fase 2. TUI: Painel [4], binding `d`.

**Dependência direta na TUI implementada** na Fase 12 (`specs/phases/phase-12-dependencia-direta/`): sem mudança no `MavenAdapter` (`update_dependency` já suportava `managed=False` desde a Fase 2) — só na TUI. `DependencyFormScreen` ganhou `title`/`managed` parametrizáveis; Painel [4] BOM + DEPENDÊNCIAS ganhou uma segunda seção somente-leitura com as dependências diretas do módulo selecionado no Painel [3], e um novo binding `m` abre o formulário já com `managed=False` para o módulo ativo (qualquer `packaging`, não só `pom`).

**Remover dependência direta pela TUI implementada** na Fase 14 (`specs/phases/phase-14-remover-dependencia-direta/`): novo `BuildToolAdapter.remove_direct_dependency(project, module_name, group_id, artifact_id)`, reaproveitando o `MavenPomWriter.remove_dependency` já existente (usado internamente por `remove_module` desde a Fase 2). TUI: `RemoveDependencyFormScreen` (formulário dedicado, só `groupId`/`artifactId`), Painel [4], binding `r`.

Ainda fora de escopo: navegar/selecionar item por item na lista de diretas (a remoção é por identificador livre, `groupId:artifactId`, mesma decisão de design já usada para diretórios na Fase 11).
