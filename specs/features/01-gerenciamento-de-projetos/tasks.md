# Feature 01 — Gerenciamento de Projetos — Tasks

Coberto pela **Fase 1** (registrar, listar, abrir em modo leitura, remover) — ver `specs/phases/phase-1-fundacao/tasks.md` (tasks T10, T11, T12).

**Criação de projeto do zero implementada** na Fase 6 (`specs/phases/phase-6-criar-projeto/`): novo `BuildToolAdapter.create_project(manifest, destination_path)`, materializa um projeto Maven multi-módulo (com BOM, dependências, diretórios convencionais/customizados) a partir de um manifesto YAML (`ModuleManifest` em `src/manager/manifest.py`, espelhando o modelo de domínio). TUI: Painel [1] PROJETOS, binding `c`.

**Exportar projeto para manifesto implementada** na Fase 7 (`specs/phases/phase-7-exportar-manifesto/`): operação inversa da Fase 6 — `to_manifest`/`dump_manifest` (`src/manager/manifest.py`, funções puras, sem passar pelo `BuildToolAdapter`, já que `Module` já é uniforme entre build tools) serializam um projeto já inferido para o mesmo formato YAML consumido por `create_project`. TUI: Painel [1] PROJETOS, binding `e`.

Fora da Fase 7 (fases futuras): clone remoto.
