# Fase 11 — Remover Diretório Não-Vazio / Caminho Livre — Design

## `DirectoryNotEmptyConflict` (`base.py`)

Nova exceção, ao lado de `DependentModuleConflict` (mesmo papel: sinalizar pra TUI "isso é destrutivo, confirme antes"):

```python
class DirectoryNotEmptyConflict(Exception):
    def __init__(self, relative_path: str):
        self.relative_path = relative_path
        super().__init__(f"'{relative_path}' nao esta vazio")
```

## `BuildToolAdapter.remove_directory` (`base.py`)

Ganha `force: bool = False`. Docstring atualizada: levanta `DirectoryNotEmptyConflict` (em vez de `ValueError`) quando não-vazio e `force=False`; com `force=True`, remove recursivamente.

## `MavenAdapter.remove_directory` (`adapter.py`)

```python
if any(target_path.iterdir()):
    if not force:
        raise DirectoryNotEmptyConflict(str(relative_path))
    shutil.rmtree(target_path)
else:
    target_path.rmdir()
```

Resto do método (validação de módulo, path-traversal, "não existe", guarda contra remover o próprio `module_dir`) inalterado. `shutil` já é importado no módulo (usado por `create_project`).

## TUI

- `MainScreen.remove_directory` passa a seguir o padrão de `remove_module`/`_do_remove`: fecha sobre `force`, tenta, captura `DirectoryNotEmptyConflict` e empilha `ConfirmModal` perguntando se remove mesmo assim; ao confirmar, rechama com `force=True`. `ValueError` continua tratado como hoje (aviso se "nao existe", erro caso contrário).
- `DirectoryFormScreen` ganha `title`/`confirm_label` opcionais (mesmo padrão já aplicado a `BuildSourceFormScreen` na Fase 10), default idêntico ao atual ("Novo diretorio"/"Criar") — não muda o call-site de criação existente.
- Novo binding em `StructurePanel`: `("x", "remove_custom_directory", "remover custom")` → `self.screen.remove_custom_directory(active_module)`.
- `MainScreen.remove_custom_directory(module)`: abre `DirectoryFormScreen(title="Remover diretorio", confirm_label="Remover")`, e no submit delega para `self.remove_directory(module, relative_path)` — mesmo caminho de código usado pelo checklist, reaproveitando o fluxo de confirmação acima sem duplicá-lo.

## Casos de borda

- `relative_path` resolvendo para o próprio `module_dir` continua bloqueado incondicionalmente (checado antes de qualquer coisa relacionada a `force`).
- Diretório vazio continua indo direto (sem `ConfirmModal`), igual à Fase 4 — só o caso não-vazio pede confirmação.

## Alternativas descartadas

- Reescrever a árvore do Painel [5] como um widget `Tree` navegável para selecionar o nó a remover — descartado por escopo desproporcional ao ganho; o caminho livre (já um padrão estabelecido nesta app desde `phase-4-diretorio-customizado`) resolve o mesmo caso de uso com muito menos código.
- Usar `ValueError` com checagem de string ("nao esta vazio") em vez de uma exceção tipada — descartado por já haver precedente (`DependentModuleConflict`) para esse exato problema (a TUI precisa distinguir "erro definitivo" de "precisa perguntar e pode prosseguir"), e checagem de string é frágil.
