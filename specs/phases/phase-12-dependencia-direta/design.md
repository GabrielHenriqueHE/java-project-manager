# Fase 12 — Dependência Direta na TUI — Design

## `DependencyFormScreen` (`dependency_form.py`)

Ganha `title`/`managed: bool = True` no construtor (mesmo padrão de parametrização já usado em `BuildSourceFormScreen`/`DirectoryFormScreen` nas Fases 10/11), em vez de sempre montar `Dependency(managed=True, ...)`:

- `title` some no lugar do `Static("Nova dependencia gerenciada (BOM)")` fixo.
- Validação: `groupId`/`artifactId` sempre obrigatórios; `version` só é obrigatória quando `managed=True` (dependência direta pode depender de uma versão vinda do BOM/`dependencyManagement`, então é opcional — mesma regra já aplicada por `MavenAdapter.update_dependency`).
- Rótulos de `type`/`scope` ficam levemente diferentes conforme `managed` (ex.: `scope` sugere `import` para gerenciada vs. `compile/provided/runtime/test` para direta) — só texto de apoio, mesmo par de campos.
- `Dependency(..., managed=self._managed)` no dismiss.

## `MainScreen`

`add_dependency` (existente, Painel [4] `n`) e o novo `add_direct_dependency` (Painel [4] `m`) compartilham um helper privado `_open_dependency_form(target_module, *, managed, title)` — só title/managed/mensagem de sucesso mudam; a chamada a `update_dependency` e o tratamento de erro são idênticos entre as duas.

```python
def add_direct_dependency(self) -> None:
    if self.project is None or self._adapter is None:
        self.notify("Nenhum projeto selecionado", severity="error")
        return
    target_module = self.selected_module or self.project.root_module
    self._open_dependency_form(
        target_module,
        managed=False,
        title=f"Nova dependencia direta de {target_module.name}",
    )
```

`target_module` reaproveita exatamente a mesma resolução já usada por `add_dependency` (`self.selected_module or self.project.root_module`) — nenhuma mudança de como o módulo-alvo é escolhido, só o `managed` muda.

## `BomPanel` (`bom_panel.py`)

Painel [4] ganha uma segunda seção, abaixo da lista de gerenciadas (BOM) existente: as dependências diretas (`managed=False`) do módulo atualmente selecionado no Painel [3]. Somente-leitura nesta fatia (sem navegação por item, sem remoção) — um `Static` simples, no mesmo estilo textual já usado por `MetadataPanel`.

- `compose_body` ganha `Static(id="direct-deps-header")` + `Static(id="direct-deps-list")` depois do `ListView` de BOM existente.
- `refresh_bom(project, selected_module=None)` ganha o parâmetro `selected_module`; a lógica de BOM existente não muda, só passa a também chamar `_render_direct_dependencies(selected_module)`.
- Novo binding `("m", "add_direct_dependency", "dep. direta")` → `self.screen.add_direct_dependency()`.

## Wiring de propagação

`MainScreen._refresh_all_panels` passa a chamar `BomPanel.refresh_bom(self.project, self.selected_module)` (antes só passava `self.project`). `MainScreen.select_module` (troca de seleção no Painel [3], sem passar por `set_project`) também chama `BomPanel.refresh_bom(self.project, module)`, para a seção de diretas acompanhar a seleção sem precisar recarregar o projeto inteiro — mesmo padrão que já atualiza só `MetadataPanel` nesse método.

## Casos de borda

- Módulo selecionado sem nenhuma dependência direta: seção mostra "nenhuma dependencia direta" (mesmo tom do `panel-empty-state` já usado em outros lugares).
- Nenhum projeto carregado: seção fica vazia (mesmo comportamento do `bom-empty` existente).
- Adicionar dependência direta com o mesmo `groupId:artifactId` de uma já existente no módulo faz upsert (atualiza `version`/`scope`/`type`), não duplica — comportamento já garantido por `MavenPomWriter.update_dependency`, nenhuma mudança necessária aqui.

## Alternativas descartadas

- Tornar a lista de diretas um `ListView` navegável com remoção nesta mesma fatia — descartado por escopo: o pedido foi "adicionar/editar"; navegação+remoção fica para uma fatia futura se o usuário pedir, seguindo o mesmo padrão incremental já usado em Estrutura de Diretórios (criar → customizado → remover → registrar → desregistrar → forçar, cada capacidade numa fatia).
- Um parâmetro `managed: bool` exposto como campo do próprio formulário (checkbox) em vez de dois pontos de entrada (`n`/`m`) — descartado por já haver precedente forte no projeto de distinguir a operação pelo binding/entry-point (ex.: `register`/`unregister` na Fase 10), não por um campo a mais pra errar.
