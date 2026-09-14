# Feature 01 — Gerenciamento de Projetos — Design

## Visão geral da solução

Um `ProjectRegistry` (em `src/manager/services/registry.py`) mantém, fora do modelo de domínio, uma lista de projetos conhecidos (path + build tool + last_opened) persistida em `~/.config/java-project-manager/registry.json`. A TUI nunca lê/escreve esse arquivo diretamente — sempre via `ProjectRegistry`.

## Modelo de domínio envolvido

- Nenhuma classe de `models.py` é usada para o registry em si (o registry é dado de aplicação, não de domínio Java). Ao abrir um projeto registrado, a entrada do registry é usada apenas para chamar `detect_adapter(path).infer_structure(path)`, que retorna um `Project` completo.

## Interface de Adapter envolvida

- `BuildToolAdapter.detect(path)` — usado ao registrar um novo projeto, para descobrir a build tool.
- `BuildToolAdapter.infer_structure(path)` — usado ao abrir um projeto para popular a `ProjectDetailScreen`.

## Fluxo

1. Usuário abre a app → `DashboardScreen` lista `ProjectRegistry.load()`.
2. Usuário escolhe "Importar/Registrar" → `ImportProjectScreen` pede um path.
3. `services/adapters_registry.detect_adapter(path)` tenta cada adapter registrado; se nenhum reconhecer o path, mostra erro.
4. Adapter encontrado → `infer_structure(path)` roda; em caso de sucesso, mostra um preview (nome, build tool, contagem de módulos) e pede confirmação.
5. Confirmado → `ProjectRegistry.add(path, build_tool)` persiste a entrada; volta ao Dashboard com o novo projeto listado.
6. Usuário seleciona um projeto no Dashboard → re-roda `infer_structure` ao vivo (não usa cache) → empurra `ProjectDetailScreen(project)`.
7. Usuário escolhe "Remover" num item do Dashboard → `ProjectRegistry.remove(path)`; nenhuma chamada ao adapter é feita.

## Impacto na camada Textual

- `screens/dashboard.py`, `screens/import_project.py`, `screens/project_detail.py` (Fase 1).

## Casos de borda

- Path já registrado → `ProjectRegistry.add` é idempotente (atualiza em vez de duplicar).
- Path do registry não existe mais no disco → Dashboard marca o item como indisponível (não remove automaticamente; remoção é sempre ação explícita do usuário).

## Alternativas consideradas e descartadas

- Persistir o registry dentro do próprio projeto Java gerenciado (ex.: `.jpm/registry.json` no repo do usuário) — descartado para não poluir repositórios de terceiros com estado da ferramenta.
