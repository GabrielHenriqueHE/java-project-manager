# Fase 9 — Marcar Diretório Registrado no Build — Tasks

- [x] **T1** — `structure_panel.py`: `_STANDARD_BY_LIST` (default por lista nomeada) e `_build_module_node` reescrito para iterar cada lista separadamente e sufixar `[dim](build)[/]` quando o diretório não é o default da sua lista.
- [x] **T2** — `tests/test_structure_panel.py` (3 casos): diretório padrão sem marcação; diretório de `source_dirs` fora do padrão marcado enquanto o padrão ao lado continua sem marcação; mesmo teste para `test_resource_dirs`.
- [x] **T3** — Atualizar `specs/features/04-estrutura-de-diretorios/tasks.md` e `specs/00-overview.md`.

## Definição de pronto

`uv run pytest`: 158 passed (155 pré-existentes + 3 novos), sem regressão; árvore do Painel [5] distingue visualmente um diretório de convenção padrão de um registrado via build-helper.
