# Fase 14 — Remover Dependência Direta na TUI — Design

## `BuildToolAdapter.remove_direct_dependency` (`base.py`)

Novo método na interface, irmão de `remove_dependency` (que é só para `managed=True`, busca global na árvore):

```python
@abstractmethod
def remove_direct_dependency(
    self, project: Project, module_name: str, group_id: str, artifact_id: str
) -> Project:
    """Remove a dependencia direta (managed=False) identificada por
    (group_id, artifact_id) de um modulo especifico.

    Levanta ValueError se o modulo nao existir ou nao tiver essa
    dependencia direta declarada.
    """
```

Diferença chave de `remove_dependency`: aqui o módulo é explícito (`module_name`), porque uma dependência direta pertence a um único pom, ao contrário da gerenciada (que `remove_dependency` localiza varrendo a árvore inteira em busca de quem a declarou no BOM).

## `MavenAdapter.remove_direct_dependency` (`adapter.py`)

```python
def remove_direct_dependency(
    self, project: Project, module_name: str, group_id: str, artifact_id: str
) -> Project:
    target = self._find_module(project.root_module, module_name)
    if target is None:
        raise ValueError(f"Modulo '{module_name}' nao encontrado no projeto")

    pom_path = project.root_path / target.build_file.path
    if not self._writer.remove_dependency(pom_path, group_id, artifact_id):
        raise ValueError(
            f"Dependencia direta '{group_id}:{artifact_id}' nao encontrada em '{target.name}'"
        )

    return self.infer_structure(project.root_path)
```

`MavenPomWriter.remove_dependency` já existe (`writer.py`, usado hoje internamente por `remove_module` para limpar dependentes) e já opera só em `<dependencies>` (nunca em `<dependencyManagement>`) — reaproveitado sem nenhuma mudança.

## TUI

- Novo modal `RemoveDependencyFormScreen` (`screens/widgets/remove_dependency_form.py`): dois campos (`groupId`, `artifactId`), sem `version`/`type`/`scope` (irrelevantes para identificar o que remover) — deliberadamente um widget novo em vez de reaproveitar `DependencyFormScreen`, que carrega campos que não fazem sentido numa remoção.
- `BomPanel`: novo binding `("r", "remove_direct_dependency", "remover direta")` → `self.screen.remove_direct_dependency()`.
- `MainScreen.remove_direct_dependency()`: mesma resolução de módulo-alvo já usada por `add_direct_dependency` (`self.selected_module or self.project.root_module`); abre `RemoveDependencyFormScreen`; no submit chama `self._adapter.remove_direct_dependency(...)`, trata `ValueError` como notificação de erro (sem `ConfirmModal` — ao contrário de `remove_module`/`remove_directory`, aqui não há efeito colateral em cascata a confirmar, é uma remoção pontual de uma única entrada).

## Casos de borda

- Módulo selecionado sem nenhuma dependência direta: `remove_dependency` do writer retorna `False` (nada para remover) → `ValueError` claro, nenhuma escrita.
- `groupId:artifactId` que existe como dependência **gerenciada** (BOM) mas não como direta no módulo selecionado: mesmo tratamento — `writer.remove_dependency` só olha `<dependencies>`, nunca `<dependencyManagement>`, então não remove por engano a entrada do BOM.

## Alternativas descartadas

- Selecionar o item a remover por navegação de lista (`ListView` na seção de diretas) — descartado pela mesma razão já registrada em `phase-12-dependencia-direta/design.md`: exigiria um mecanismo de alternar foco entre duas listas dentro do Painel [4], e `tab` já está reservado para navegar entre painéis nesta app.
- Reaproveitar `DependencyFormScreen` passando `managed=False` e ignorando os campos extras no submit — descartado por poluir a UI com campos (version/type/scope) que não fazem sentido para uma remoção; um formulário dedicado e menor é mais claro.
