# Fase 3 — Reformulação da TUI — Design

## Arquitetura geral

Uma única tela `MainScreen` (`src/manager/screens/main_screen.py`) substitui `DashboardScreen`+`ProjectDetailScreen`. `ManagerApp.on_mount` passa a empurrar `MainScreen` em vez de `DashboardScreen`. `dashboard.py`, `project_detail.py` e seus testes (`test_app_dashboard.py`, `test_project_detail_remove_module.py`, `test_project_detail_add_module.py`) são removidos — substituídos por `test_main_screen.py`.

`MainScreen` mantém o estado compartilhado entre painéis:
- `registry: ProjectRegistry`
- `project: Project | None` (projeto atualmente selecionado, `None` se nenhum registrado/selecionado)
- `selected_module: Module | None` (módulo selecionado no Painel 3, direciona o Painel 2)
- `structure_active_module: Module | None` (módulo "ativo" do Painel 5, alternado por `space`, independente de `selected_module`)

Os 5 painéis são widgets filhos que **leem** esse estado via referência à `MainScreen` (`self.screen` ou passado no construtor) e nunca mutam arquivos diretamente — toda mutação passa por `detect_adapter(project.root_path)` + método do adapter, igual às Fases 1-2. Após qualquer mutação, `MainScreen.set_project(adapter.infer_structure(root_path))` propaga o novo `Project` para todos os painéis (cada painel implementa `refresh(project, selected_module, ...)` chamado pela `MainScreen`).

## Widget de painel reutilizável

`src/manager/screens/widgets/panel.py`: classe base `Panel(Vertical)` com:
- Um `Static` de header com duas partes (título fixo `[n] TITULO` à esquerda, um texto dinâmico à direita definido por `set_header_right(text: str)`).
- `DEFAULT_CSS` com borda simples (`border: round $primary;`), sem sombra.
- `can_focus = True` para participar do ciclo de foco/Footer contextual.

Cada painel concreto herda de `Panel` e implementa seu próprio corpo (lista, tabela, etc.) abaixo do header.

## Painéis

### `ProjectsPanel` (`widgets/projects_panel.py`) — Painel 1
- Corpo: `ListView` de `ListItem(Label(...))`, um item por `RegistryEntry`. Marcador `●`/`○` calculado comparando `entry.path` com `project.root_path` atual.
- `BINDINGS`: `("n", "import_project", "novo")`, `("d", "remove_project", "remover")`, `("j", "cursor_down", "mover")`, `("k", "cursor_up", "mover")`.
- Header direito: `f"{len(entries)} repos"`.
- Estado vazio: `Static("carregando…")` (nenhuma entrada no registry).
- Ao mudar o item destacado (`ListView.Highlighted`), chama `main_screen.select_project(entry)`.

### `ModulesPanel` (`widgets/modules_panel.py`) — Painel 3
- Corpo: `ListView` populado por uma função `_flatten(module, depth, is_last_chain) -> list[(prefix, module)]` que percorre a árvore em pré-ordem e calcula o prefixo `"├─ "`/`"└─ "`/`"│  "` por profundidade (mesma técnica usada em CLIs de árvore de arquivos: para cada nível, sabe se o nó é o último filho do seu pai para decidir entre `├─`/`└─`, e acumula `"│  "` ou `"   "` para os níveis ancestrais).
- Item: `f"{prefix}{module.name}  {module.metadata.packaging}"` (packaging em estilo secundário via markup `[dim]`).
- `BINDINGS`: `("n", "add_module", "novo")`, `("d", "remove_module", "remover")`, `("j", "cursor_down", "mover")`, `("k", "cursor_up", "mover")`, `("enter", "select", "abrir/editar")` — na prática `ListView` já trata enter/click como "highlight"; `select` apenas confirma e propaga para `main_screen.select_module(...)`.
- Header direito: nome do projeto ativo.
- Estado vazio: "nenhum projeto selecionado".

### `MetadataPanel` (`widgets/metadata_panel.py`) — Painel 2
- Corpo: `Static` com texto formatado em duas colunas (chave em `[dim]`, valor alinhado). Campos: name, groupId, artifactId, version, `java.version` (lido de `metadata.properties.get("maven.compiler.source")` como aproximação, documentado no código), packaging, description.
- `BINDINGS`: `("enter", "edit", "edita")` — a ação mostra `self.notify("Edicao de metadados ainda nao implementada (Fase 2 seguinte)", severity="warning")`.
- Header direito: fixo `"enter edita"` (o hint já está sempre correto, independente de estado).
- Estado vazio: "nenhum projeto selecionado".
- `refresh(module)` é chamado por `main_screen.select_module`.

### `BomPanel` (`widgets/bom_panel.py`) — Painel 4
- Corpo: `ListView` sobre `project.managed_dependencies` (não sobre um módulo específico — é uma visão de projeto inteiro, como já modelado desde a Fase 1). Cada item: `f"bom {dep.group_id}:[b]{dep.artifact_id}[/b] {dep.version} · {dep.scope or 'import'}"`.
- `BINDINGS`: `("n", "add_dependency", "novo")` → notifica "ainda nao implementado"; sem bind de `d` (ver decisão registrada em `specs/design/tui-layout.md`).
- Header direito: nome do módulo com `is_bom=True` encontrado na árvore (busca recursiva, reaproveitando o padrão de `MavenAdapter._find_bom_module` — implementada aqui como função utilitária independente já que é lógica de apresentação, não do adapter).
- Estado vazio: "nada declarado. pressione n".

### `StructurePanel` (`widgets/structure_panel.py`) — Painel 5
- Corpo dividido em dois `Static`/`RichLog` internos (sem borda entre eles): checklist (8 linhas fixas) + árvore textual.
- Checklist: para o `structure_active_module` atual, verifica a existência em disco de cada um dos 8 caminhos fixos (`project.root_path / active_module.relative_path / <caminho>`), renderiza `[x]`/`[ ]`.
- Árvore textual: função `render_project_tree(project) -> str` (`src/manager/screens/widgets/structure_panel.py` ou um helper dedicado) que percorre `project.root_module` recursivamente e, para cada módulo, lista `pom.xml` (com `"(packaging: pom)"` se aplicável) e as pastas-fonte presentes, colapsando cadeias de diretórios com um único filho e sem arquivos em uma linha só (`br/com/orion/orionbom/`), no estilo `├──`/`│`/`└──`.
- `BINDINGS`: `("space", "toggle_active_module", "alterna")`.
- Header direito: `f"space alterna · {structure_active_module.name}"`.
- Estado vazio: "sem modulos. pressione n" (só quando o projeto não tem nenhum módulo além da raiz — na prática nunca acontece com Maven, mas o estado é tratado).

## Cabeçalho customizado

`src/manager/screens/widgets/app_header.py`: `AppHeader(Static)` (não usa o `Header` nativo). `compose`/`render` monta uma `Horizontal` com dois `Static`: esquerdo (`"[b]mvnforge[/b] {coordenada}"`, coordenada = `f"{groupId}:{artifactId}:{version}"` do módulo raiz) e direito (`f"java {java_version} · maven · {n_mod} mod · {n_dep} dep"`, alinhado à direita via `text-align: right` no CSS). `java_version` lido de `properties.get("maven.compiler.source")` ou `"?"` se ausente. `n_mod` = total de módulos (incluindo raiz); `n_dep` = soma de dependências diretas de todos os módulos (não conta `managed`, para não contar a mesma entrada duas vezes).

## Rodapé e modo comando

- `Footer()` nativo do Textual, sem BINDINGS na `App`/`MainScreen` — só nos painéis, para o contexto mudar com o foco (conforme já validado no design).
- Badge "PAINEL N" + status: como o `Footer` nativo não tem um slot nativo para isso à esquerda, implementamos uma `Static` fixa e pequena posicionada entre o corpo e o `Footer` (ou substituímos o footer por um widget composto `Horizontal(Static(badge), Footer())`), atualizada via `on_descendant_focus`/reactive var `focused_panel_number`.
- Modo comando: `CommandBar(Input)` (`src/manager/screens/widgets/command_bar.py`), oculto por padrão (`display: none`), toggled por um binding global `(":", "toggle_command_mode", "comando")` declarado na própria `MainScreen` (único bind verdadeiramente global, já que não pertence a nenhum painel específico). Ao ativar, esconde o footer/badge e mostra o `CommandBar` com foco automático e placeholder `f":<contexto> > digite e pressione enter · esc cancela"`. `esc` (bind local do `CommandBar`) cancela e volta ao modo normal. `enter` despacha `MainScreen.run_command(text)`:
  - `"modulo <nome>"` → chama `add_module` com `parent_name=selected_module.name` (ou projeto raiz se nada selecionado), artifactId=`<nome>`, demais campos default.
  - Qualquer outro texto → `self.notify(f"Comando nao reconhecido ou nao implementado: {text}", severity="warning")`.

## Reuso de componentes existentes

- `ImportProjectScreen`, `ModuleFormScreen`, `ConfirmModal`: reaproveitados sem alteração de lógica interna — apenas o *caller* muda (de `DashboardScreen`/`ProjectDetailScreen` para os painéis 1/3 dentro de `MainScreen`).
- `ProjectRegistry`, `detect_adapter`, `MavenAdapter`: inalterados.
- `ProjectTree` (widget de árvore da Fase 1) e `screens/dashboard.py`/`screens/project_detail.py`: removidos, substituídos pela renderização manual de conectores em `ModulesPanel` e pela árvore textual de `StructurePanel`.

## Testes

`tests/test_main_screen.py` cobre, via `App.run_test()`:
- Estados vazios de todos os painéis sem projeto registrado.
- Importar projeto (Painel 1, `n`) popula todos os painéis.
- Navegar módulos (Painel 3, `j`/`k`/`enter`) atualiza o Painel 2.
- Adicionar módulo (Painel 3, `n`) e remover módulo (Painel 3, `d`, incluindo o caminho de conflito) continuam funcionando como nas Fases 1-2.
- Alternar módulo ativo do Painel 5 (`space`).
- Ativar/cancelar modo comando (`:`, `esc`) e executar `modulo <nome>`.
