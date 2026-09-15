# Fase 4 — Estrutura de Diretórios — Design

## `BuildToolAdapter.add_directory` (`src/manager/adapters/base.py`)

Novo método abstrato:

```python
@abstractmethod
def add_directory(
    self, project: Project, module_name: str, relative_path: Path
) -> Project:
    """Cria relative_path (relativo a raiz do modulo) em disco.

    Levanta ValueError se o modulo nao existir, se o diretorio ja
    existir, ou se relative_path escapar do diretorio do modulo.
    """
```

Assim como `add_module`/`remove_module`/`update_dependency`/`update_metadata`, entra na interface para que uma futura `GradleAdapter` possa ter uma implementação diferente (ex.: Gradle pode precisar registrar um `sourceSet` customizado em `build.gradle`, algo que Maven não exige para uma pasta simples).

## `MavenAdapter.add_directory`

Fluxo (`src/manager/adapters/maven/adapter.py`):

1. `_find_module(root_module, module_name)` — `ValueError` se não encontrado (reaproveitado).
2. `module_dir = project.root_path / target.relative_path`; `target_path = (module_dir / relative_path).resolve()`.
3. Validação de path traversal: `target_path` precisa estar dentro de `module_dir.resolve()` (`target_path.is_relative_to(module_dir.resolve())`, Python 3.9+) — senão `ValueError` claro, nenhuma escrita.
4. Se `target_path.exists()` → `ValueError` ("diretorio ja existe") — mesma convenção de erro-claro-sem-escrita usada em `add_module`.
5. `target_path.mkdir(parents=True)`.
6. Retorna `self.infer_structure(project.root_path)`.

Não há nenhuma escrita de XML nesta operação — é a primeira mutação do adapter que não toca em nenhum `pom.xml`.

## TUI (`src/manager/screens/widgets/structure_panel.py`)

- `StructurePanel` ganha um segundo índice de cursor, `_checklist_index`, separado de `_active_index` (que já existe e seleciona o **módulo**). `_checklist_index` seleciona o **item do checklist** dentro do módulo ativo.
- Novos bindings: `("j", "cursor_down", "mover")`, `("k", "cursor_up", "mover")`, `("enter", "create_selected", "criar")`. `space` continua com `action_toggle_active_module` (alterna módulo).
- `_render_checklist` passa a destacar visualmente o item em `_checklist_index` (mesmo padrão de fundo/cor usado nos outros painéis para o item selecionado).
- `action_cursor_down`/`action_cursor_up`: `_checklist_index = (_checklist_index + 1) % len(_CHECKLIST_DIRS)` (e `-1 % len` para cima); re-renderiza.
- `action_create_selected`: delega para `self.screen.add_directory(active_module, _CHECKLIST_DIRS[_checklist_index])`.
- `MainScreen.add_directory(module: Module, relative_path: str) -> None` (novo, mesmo padrão de `add_module`/`update_metadata`): chama `self._adapter.add_directory(self.project, module.name, Path(relative_path))`; em sucesso, `self.notify(f"'{relative_path}' criado")` + `self.set_project(updated)`; captura `ValueError` — mas o caso "diretório já existe" é tratado como aviso informativo (`severity="warning"`, mensagem "'{relative_path}' ja existe"), não como erro, já que não é uma falha real do ponto de vista do usuário (ver critério de aceite: repetir a ação num item já criado não deve parecer um erro).

## Casos de borda tratados

- Item do checklist já existente: `MavenAdapter.add_directory` levanta `ValueError`; `MainScreen.add_directory` distingue essa mensagem (por prefixo/conteúdo) das demais para notificar como aviso, não erro — evita que uma ação idempotente pareça uma falha.
- Criar `src/main/webapp` sem `src/main` existir ainda: `mkdir(parents=True)` cria a cadeia inteira numa chamada.
- Módulo sem nenhum diretório ainda (`packaging=pom` puro): checklist mostra todos os itens como ausentes; criar qualquer um funciona normalmente.
- `_checklist_index` fora dos limites após trocar de módulo ativo (`space`): resetado para `0` sempre que `_active_index` muda, evitando index out of range.
