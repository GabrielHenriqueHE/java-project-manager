# Fase 5 — Remover Dependência — Design

## `BuildToolAdapter.remove_dependency` (`src/manager/adapters/base.py`)

```python
@abstractmethod
def remove_dependency(
    self, project: Project, group_id: str, artifact_id: str
) -> Project:
    """Remove a dependencia gerenciada (managed=True) identificada por
    (group_id, artifact_id), em qualquer modulo do projeto que a declare.

    Levanta ValueError se nenhum modulo tiver essa dependencia gerenciada.
    """
```

## `MavenAdapter.remove_dependency`

Fluxo (`src/manager/adapters/maven/adapter.py`):

1. `_find_managed_dependency_owner(project.root_module, group_id, artifact_id)` (novo método privado, mesmo padrão de busca recursiva de `_find_bom_module`/`_find_dependents`): percorre a árvore, retorna o primeiro `Module` cujo `.dependencies` contenha um `Dependency` com `managed=True` e `(group_id, artifact_id)` batendo.
2. Se `None` → `ValueError` ("dependencia gerenciada nao encontrada").
3. `pom_path = project.root_path / owner.build_file.path`.
4. `self._writer.remove_managed_dependency(pom_path, group_id, artifact_id)` — método já existente (Fase 2 — remover módulo), sem nenhuma mudança.
5. Retorna `self.infer_structure(project.root_path)`.

## TUI

### `BomPanel` (`src/manager/screens/widgets/bom_panel.py`)

- Passa a guardar a lista de dependências renderizadas (`self._dependencies: list[Dependency]`), populada em `refresh_bom`, mesmo padrão de `ModulesPanel._modules`/`module_at`.
- Novo método `dependency_at(index: int | None) -> Dependency | None`, espelhando `ModulesPanel.module_at`.
- Novo binding `("d", "remove_dependency", "remover")`.
- `action_remove_dependency`: pega o índice do `#bom-list` (`ListView.index`), resolve via `dependency_at`, se não for `None` chama `self.screen.remove_dependency(dependency)`.

### `MainScreen.remove_dependency`

```python
def remove_dependency(self, dependency: Dependency) -> None:
    if self.project is None or self._adapter is None:
        self.notify("Nenhum projeto selecionado", severity="error")
        return
    try:
        updated = self._adapter.remove_dependency(
            self.project, dependency.group_id, dependency.artifact_id
        )
    except ValueError as exc:
        self.notify(str(exc), severity="error")
        return
    self.notify(f"Dependencia '{dependency.artifact_id}' removida")
    self.set_project(updated)
```

Mesmo padrão das demais mutações (erro do adapter vira notificação, sucesso atualiza o projeto). Sem distinção aviso/erro aqui (ao contrário de `add_directory`/`remove_directory`) porque não há um caso "idempotente" plausível pela UI — a entrada sempre existe na lista antes de `d` ser pressionado.

## Casos de borda tratados

- Última entrada gerenciada de um módulo removida: `BomPanel.refresh_bom` já trata a lista vazia (estado "nada declarado. pressione n" já existente).
- Dependência não encontrada (chamada direta ao adapter, fora do fluxo normal da TUI): erro claro, nenhuma escrita.

## Bug encontrado e corrigido durante a implementação

`BomPanel.refresh_bom` populava `#bom-list` via `list_view.append(...)` mas nunca setava `list_view.index` — diferente de `ProjectsPanel`/`ModulesPanel`, que já sofreram esse mesmo problema na Fase 3 (ver notas de `phase-3-redesign-tui/tasks.md`) e o corrigiram. Como `action_add_dependency` não dependia do índice selecionado, o bug ficou invisível até esta fatia: `dependency_at(list_view.index)` sempre recebia `None` e `action_remove_dependency` virava um no-op silencioso. Corrigido setando `list_view.index = 0` ao final de `refresh_bom` quando há itens.
