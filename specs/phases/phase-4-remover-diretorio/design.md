# Fase 4 — Remover Diretório — Design

## `BuildToolAdapter.remove_directory` (`src/manager/adapters/base.py`)

```python
@abstractmethod
def remove_directory(
    self, project: Project, module_name: str, relative_path: Path
) -> Project:
    """Remove relative_path (relativo a raiz do modulo) do disco, se vazio.

    Levanta ValueError se o modulo nao existir, se relative_path escapar
    do diretorio do modulo, se o diretorio nao existir, ou se nao
    estiver vazio.
    """
```

## `MavenAdapter.remove_directory`

Fluxo (`src/manager/adapters/maven/adapter.py`), espelhando `add_directory`:

1. `_find_module` — `ValueError` se não encontrado.
2. Resolve `module_dir`/`target_path` e valida path traversal (mesma lógica de `add_directory`, extraída para um helper privado `_resolve_module_relative_path` reaproveitado pelos dois métodos).
3. `ValueError` se `relative_path` resolver para o próprio `module_dir` (remove_directory não remove o módulo inteiro).
4. `ValueError` ("nao existe") se `target_path` não existir.
5. `ValueError` ("nao esta vazio") se `any(target_path.iterdir())`.
6. `target_path.rmdir()`.
7. Retorna `self.infer_structure(project.root_path)`.

## Refatoração pequena: `_resolve_module_relative_path`

`add_directory` e `remove_directory` compartilham a mesma resolução/validação de `relative_path` (traversal guard). Extraído como método privado:

```python
def _resolve_module_relative_path(
    self, project: Project, target: Module, relative_path: Path
) -> Path:
    module_dir = (project.root_path / target.relative_path).resolve()
    target_path = (module_dir / relative_path).resolve()
    if module_dir not in (target_path, *target_path.parents):
        raise ValueError(
            f"'{relative_path}' escapa do diretorio do modulo '{target.name}'"
        )
    return target_path
```

`add_directory` passa a chamar esse helper (comportamento idêntico, só reaproveitado).

## TUI (`src/manager/screens/widgets/structure_panel.py`)

- Novo binding `("d", "remove_selected", "remover")`.
- `action_remove_selected`: mesmo padrão de `action_create_selected` — resolve módulo ativo e item do checklist destacado, delega para `self.screen.remove_directory(active_module, relative_path)`.

## `MainScreen.remove_directory`

```python
def remove_directory(self, module: Module, relative_path: str) -> None:
    if self.project is None or self._adapter is None:
        self.notify("Nenhum projeto selecionado", severity="error")
        return
    try:
        updated = self._adapter.remove_directory(
            self.project, module.name, Path(relative_path)
        )
    except ValueError as exc:
        severity = "warning" if "nao existe" in str(exc) else "error"
        self.notify(str(exc), severity=severity)
        return
    self.notify(f"'{relative_path}' removido")
    self.set_project(updated)
```

Mesmo padrão de distinguir "aviso" (nada a fazer, ex.: item já ausente) de "erro" (algo bloqueou de verdade, ex.: não está vazio) já usado em `add_directory`.

## Casos de borda tratados

- Item do checklist já ausente: aviso, não erro; nenhuma escrita.
- Item com conteúdo: erro claro ("nao esta vazio"), nenhuma remoção.
- `relative_path` que escapa do módulo: erro claro, mesma proteção de `add_directory`.
- `relative_path` resolvendo para o próprio `module_dir`: erro claro, nunca remove o módulo inteiro.
