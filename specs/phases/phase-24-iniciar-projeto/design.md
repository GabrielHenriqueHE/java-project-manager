# Fase 24 — Iniciar Projeto do Zero — Design

## Novo `InitProjectScreen`

`src/manager/screens/init_project.py` segue a mesma família de `CreateProjectScreen`/`ImportProjectScreen`/`CloneProjectScreen`: um `Screen[bool]` completo (`Header`/`Footer`, não `ModalScreen` — essa distinção já existe na base entre telas de "fluxo de nível de projeto" e os modais de mutação dentro de um projeto já aberto, como `DependencyFormScreen`/`DirectoryFormScreen`). `_do_create` monta um `ModuleManifest` inteiramente em memória:

```python
manifest = ModuleManifest(
    metadata=ProjectMetadata(
        group_id=group_id,
        artifact_id=artifact_id,
        version=version,
        packaging="jar",
    ),
)
```

Os demais campos de `ModuleManifest` (`dependencies`, `directory_structure`, `submodules`) ficam nos seus defaults (`Field(default_factory=...)`): lista vazia, `DirectoryStructure()` padrão (`src/main/java` etc., convenção idêntica entre Maven e Gradle desde a Fase 15) e nenhum submódulo. Isso não exige nenhuma mudança em `MavenAdapter.create_project`/`GradleAdapter.create_project` — ambos já tratam esse manifesto mínimo corretamente (é essencialmente o mesmo shape que os testes de "módulo único, sem dependências" de cada adapter já exercitam desde as Fases 6/23).

O adapter é escolhido diretamente pelo campo de build tool do formulário (`MavenAdapter()` ou `GradleAdapter()`), sem passar por `detect_adapter` — não há nada em disco ainda para detectar a partir dele, mesmo caso de `CreateProjectScreen` hoje (que só nunca ofereceu a escolha).

## Por que sem `Select`

Nenhum formulário existente na base usa o widget `Select` do Textual (confirmado por grep em `screens/widgets/*.py`). O precedente estabelecido para "escolher um de um conjunto fixo de valores" é um `Input` livre validado contra um set hardcoded, como `_VALID_ROLES` em `screens/widgets/build_source_form.py`. O campo de build tool segue o mesmo padrão (`_VALID_BUILD_TOOLS = {"maven", "gradle"}`), mantendo consistência visual/de código com o resto da TUI em vez de introduzir um widget novo para um único campo.

## Validação: nada duplicado da regra de negócio

A tela intencionalmente só valida o que é puramente sintático (build tool reconhecida, artifactId não-vazio, destino não-vazio) — tudo que é regra de negócio real (Maven exigindo groupId/version na raiz, destino já existente e não-vazio) é deixado para o `ValueError` que o adapter já levanta, propagado direto pro `Static` de feedback. Mesmo padrão que `CreateProjectScreen._do_create` já usa para os erros de `load_manifest`/`create_project`.

## Wiring

`ProjectsPanel` (`screens/widgets/projects_panel.py`) ganha o binding `i` ("iniciar", confirmado livre em todo o app via grep nas `BINDINGS` de todos os painéis):

```python
BINDINGS = [
    ("n", "import_project", "novo"),
    ("i", "init_project", "iniciar"),
    ("c", "create_project", "criar"),
    ...
]

def action_init_project(self) -> None:
    self.screen.init_project()
```

`MainScreen.init_project()` reaproveita `_on_project_registered` diretamente (mesmo padrão de `import_project`/`clone_project`, que não duplicam a lógica de "recarregar lista + selecionar o último" como `create_project()` faz com seu `_on_dismiss` local):

```python
def init_project(self) -> None:
    self.app.push_screen(InitProjectScreen(self.registry), self._on_project_registered)
```

## Decisão: `CreateProjectScreen` não muda nesta fase

`CreateProjectScreen` continua hardcoded em `MavenAdapter()` — gap conhecido desde que `GradleAdapter.create_project` ficou pronto na Fase 23, mas deliberadamente fora do escopo aqui: são fluxos independentes (um consome manifesto YAML, o outro monta o manifesto em memória a partir de um formulário), corrigir os dois juntos misturaria o motivo de cada mudança e arriscaria regressão nos testes já verdes de `CreateProjectScreen`. Fica registrado como candidato a uma fatia futura própria.

## Testes

Casos novos em `tests/test_main_screen.py` (mesma convenção já usada para `create_project`/`import_project`/`clone_project` nesse arquivo — sem arquivo de teste separado), reaproveitando o fixture `_TestApp`/`ProjectRegistry(tmp_path / "registry.json")` já existente: criação Maven de ponta a ponta, criação Gradle de ponta a ponta, artifactId ausente, Maven sem groupId/version (erro do adapter), destino já existente e não-vazio (erro do adapter), build tool inválida, e cancelamento não cria nada.
