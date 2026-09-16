# Feature 01 — Gerenciamento de Projetos — Tasks

Coberto pela **Fase 1** (registrar, listar, abrir em modo leitura, remover) — ver `specs/phases/phase-1-fundacao/tasks.md` (tasks T10, T11, T12).

**Criação de projeto do zero implementada** na Fase 6 (`specs/phases/phase-6-criar-projeto/`): novo `BuildToolAdapter.create_project(manifest, destination_path)`, materializa um projeto Maven multi-módulo (com BOM, dependências, diretórios convencionais/customizados) a partir de um manifesto YAML (`ModuleManifest` em `src/manager/manifest.py`, espelhando o modelo de domínio). TUI: Painel [1] PROJETOS, binding `c`.

**Exportar projeto para manifesto implementada** na Fase 7 (`specs/phases/phase-7-exportar-manifesto/`): operação inversa da Fase 6 — `to_manifest`/`dump_manifest` (`src/manager/manifest.py`, funções puras, sem passar pelo `BuildToolAdapter`, já que `Module` já é uniforme entre build tools) serializam um projeto já inferido para o mesmo formato YAML consumido por `create_project`. TUI: Painel [1] PROJETOS, binding `e`.

**Código-fonte na exportação implementado** na Fase 8 (`specs/phases/phase-8-codigo-fonte-exportacao/`): `export_source_files` (`src/manager/manifest.py`) copia os diretórios rastreados dos módulos que batem com um padrão de nome (glob, ex. `shared-*`) para uma pasta irmã do manifesto (`<manifest>.files/<artifactId>/...`); `create_project` ganhou `source_root` opcional para copiar esses arquivos reais em vez de só criar diretórios vazios ao recriar o projeto. TUI: campo de padrão no formulário de exportação; detecção automática da pasta `.files` no formulário de criação.

Fora da Fase 8 (fases futuras): clone remoto.
