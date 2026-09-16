# Fase 7 — Exportar Projeto para Manifesto — Design

## `src/manager/manifest.py` — duas funções novas

```python
def to_manifest(module: Module) -> ModuleManifest:
    """Converte um Module ja inferido (uniforme entre build tools) para o
    formato de manifesto - inverso de como create_project materializa um
    ModuleManifest. Descarta os campos que so existem em disco
    (relative_path, build_file) e o `tree` de DirectoryStructure (so serve
    para exibicao da arvore no Painel [5]; create_project nunca le `tree`
    na materializacao).
    """
    directory_structure = module.directory_structure.model_copy(update={"tree": None})
    return ModuleManifest(
        metadata=module.metadata,
        dependencies=module.dependencies,
        directory_structure=directory_structure,
        submodules=[to_manifest(sub) for sub in module.submodules],
    )


def dump_manifest(manifest: ModuleManifest, path: Path) -> None:
    """Serializa o manifesto para YAML em path, sobrescrevendo se existir."""
    data = manifest.model_dump(mode="json", exclude_defaults=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
```

- `directory_structure.model_copy(update={"tree": None})`: `Module.directory_structure` é o mesmo tipo `DirectoryStructure` que `ModuleManifest.directory_structure` espera, então não há remapeamento campo a campo — só zera `tree` (o único campo que não faz sentido como entrada, ver requirements). `model_copy` evita mutar o `DirectoryStructure` do `Module` original (que ainda pertence ao `Project` em memória usado pela TUI).
- `metadata`/`dependencies` são atribuídos diretamente — mesmos tipos Pydantic (`ProjectMetadata`, `list[Dependency]`) dos dois lados, zero conversão.
- `model_dump(mode="json", exclude_defaults=True)`: `mode="json"` garante tipos serializáveis (não há `Path` em `ModuleManifest`, mas mantém o padrão já usado em `ProjectRegistry.save`, `registry.py:36`, para consistência). `exclude_defaults=True` omite campos iguais ao default do model (`packaging: "jar"`, listas vazias, `managed: false`, etc.) — YAML final enxuto, no mesmo estilo que um manifesto escrito à mão para `create_project` (Fase 6) teria.
- `path.parent.mkdir(parents=True, exist_ok=True)`: só garante que o diretório-pai do arquivo de destino exista (não é a mesma checagem de `destination_path` vazio de `create_project` — aqui não há árvore de código para proteger, só um arquivo).

Import novo no topo do módulo: nenhum (já importa `yaml`, `Path`, `BaseModel`/`Field` de pydantic). Precisa de `from manager.models import Module` além dos imports já existentes (`Dependency`, `DirectoryStructure`, `ProjectMetadata`).

## TUI

### `ExportManifestScreen` (`src/manager/screens/export_manifest.py`, novo)

Mesmo padrão estrutural de `CreateProjectScreen`/`ImportProjectScreen` (`Screen[bool]`, `Header`/`Vertical`/`Footer`, binding `escape` → `app.pop_screen`), mas recebe o `Project` já carregado em vez de reconstruir/reler nada:

```python
class ExportManifestScreen(Screen[bool]):
    def __init__(self, project: Project):
        super().__init__()
        self._project = project

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static(f"Exportar '{self._project.name}' para:"),
            Input(placeholder="/caminho/para/manifest.yaml", id="destination-input"),
            Static(id="export-feedback"),
            Button("Exportar", id="confirm-export", variant="primary"),
            id="export-form",
        )
        yield Footer()

    @on(Input.Submitted, "#destination-input")
    def _submit_via_enter(self) -> None:
        self._do_export()

    @on(Button.Pressed, "#confirm-export")
    def _submit_via_button(self) -> None:
        self._do_export()

    def _do_export(self) -> None:
        raw_path = self.query_one("#destination-input", Input).value.strip()
        feedback = self.query_one("#export-feedback", Static)
        if not raw_path:
            feedback.update("[red]Informe o caminho de destino.[/red]")
            return

        path = Path(raw_path).expanduser()
        manifest = to_manifest(self._project.root_module)
        try:
            dump_manifest(manifest, path)
        except OSError as exc:
            feedback.update(f"[red]Falha ao exportar: {exc}[/red]")
            return

        feedback.update(f"[green]Exportado para {path}[/green]")
        self.set_timer(0.6, self._finish)

    def _finish(self) -> None:
        self.dismiss(True)
```

Não há validação de "arquivo já existe" (decisão: sobrescreve sem perguntar) nem chamada a nenhum adapter — só `to_manifest` + `dump_manifest`, ambas puras/sem I/O de build.

### `ProjectsPanel` (`src/manager/screens/widgets/projects_panel.py`)

Novo binding `("e", "export_project", "exportar")` na lista `BINDINGS` (depois de `c`, antes de `d`, mesma ordem de aparição no rodapé que os outros). `action_export_project`:

```python
def action_export_project(self) -> None:
    self.screen.export_project()
```

### `MainScreen.export_project` (`src/manager/screens/main_screen.py`)

```python
def export_project(self) -> None:
    if self.project is None:
        self.notify("Nenhum projeto selecionado", severity="error")
        return

    def _on_dismiss(exported: bool | None) -> None:
        pass  # nada a atualizar no estado da tela apos exportar

    self.app.push_screen(ExportManifestScreen(self.project), _on_dismiss)
```

Ao contrário de `create_project`/`import_project`, o callback de dismiss não precisa recarregar nada (`self.project`/`self.registry` não mudam — exportar não altera o projeto nem o registry). Import novo: `from manager.screens.export_manifest import ExportManifestScreen`.

## Casos de borda tratados

- Diretório-pai do caminho de destino não existe ainda: `dump_manifest` cria com `mkdir(parents=True, exist_ok=True)` antes de escrever, mesma conveniência de outras operações de escrita (ex.: `create_pom`).
- Caminho de destino sem permissão de escrita ou inválido: `OSError` capturado no form, feedback claro, projeto em memória inalterado.
- Projeto com módulo BOM: `dependencies` do módulo BOM já inclui as entradas `managed=True` (mesma estrutura usada por `create_project`), então o round-trip preserva o BOM sem tratamento especial.
- Campo vazio no form: mesma validação client-side já usada em `CreateProjectScreen`/`ImportProjectScreen` (feedback, sem tentar exportar).
