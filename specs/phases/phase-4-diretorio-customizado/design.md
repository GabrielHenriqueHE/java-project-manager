# Fase 4 — Diretório Customizado — Design

## `DirectoryFormScreen` (`src/manager/screens/widgets/directory_form.py`, novo)

`ModalScreen[str | None]`, mesmo padrão visual de `ModuleFormScreen`/`MetadataFormScreen`/`DependencyFormScreen`: um `Input` (`#field-path`, placeholder `ex.: src/main/proto`), `Static` de feedback, botões `Criar`/`Cancelar`. Confirmar com o campo vazio mostra feedback e não fecha o modal; com valor, `dismiss(path.strip())`. Cancelar `dismiss(None)`.

## `StructurePanel`

- Novo binding `("n", "add_custom_directory", "novo")`.
- `action_add_custom_directory`: resolve o módulo ativo (`self._modules[self._active_index]`, mesmo padrão de `action_create_selected`) e chama `self.screen.add_custom_directory(active_module)`.

## `MainScreen.add_custom_directory`

```python
def add_custom_directory(self, module: Module) -> None:
    if self.project is None or self._adapter is None:
        self.notify("Nenhum projeto selecionado", severity="error")
        return

    def _on_submit(relative_path: str | None) -> None:
        if relative_path is None:
            return
        self.add_directory(module, relative_path)

    self.app.push_screen(DirectoryFormScreen(), _on_submit)
```

Reaproveita `MainScreen.add_directory` (já existente, `phase-4-estrutura-diretorios`) para a mutação em si — este método novo é só a ponte entre o formulário de caminho livre e a operação já implementada/testada. Nenhuma mudança em `MavenAdapter`/`MavenPomWriter`.

## Casos de borda tratados

- Campo vazio: barrado no próprio formulário, nenhuma chamada ao adapter.
- Caminho duplicado/traversal: mesmo comportamento já coberto pelos testes de `MainScreen.add_directory`/`MavenAdapter.add_directory` da fatia anterior — não há novo caso de borda na camada de domínio, só um novo caminho de UI até o método existente.
