# Fase 2 — Remover Módulo — Design

## Camada de escrita XML (`src/manager/adapters/maven/`)

- `xml_utils.py` (novo, extraído do que já existia em `parser.py`): `namespace_of(root)` e `remove_element_preserving_whitespace(elem)` — este último reatribui o `tail` (texto/whitespace após a tag de fechamento) do elemento removido ao irmão anterior (ou ao `.text` do pai, se for o primeiro filho), evitando linhas em branco no lugar do elemento removido.
- `writer.py` (novo): `MavenPomWriter` com três operações pontuais, cada uma lê o pom, aplica uma mutação, grava de volta:
  - `remove_module_entry(pom_path, module_value)` — remove `<module>module_value</module>` de `<modules>`; se `<modules>` ficar vazio, remove `<modules>` também.
  - `remove_managed_dependency(pom_path, group_id, artifact_id)` — remove a entrada correspondente em `<dependencyManagement><dependencies>`; limpa `<dependencies>` e `<dependencyManagement>` se ficarem vazios.
  - `remove_dependency(pom_path, group_id, artifact_id)` — mesma lógica para `<dependencies>` diretas do módulo (não dentro de `dependencyManagement`).
  - Após escrever, normaliza a declaração XML (`'` → `"`) para reduzir diff cosmético — ver limitação sobre a tag `<project>` em `requirements.md`.

## `MavenAdapter.remove_module`

Fluxo (`src/manager/adapters/maven/adapter.py`):

1. `_find_module(root_module, module_name)` — busca recursiva pelo nome; `ValueError` se não encontrado.
2. `_find_parent(root_module, target)` — acha o módulo cujo `submodules` contém o alvo (comparando por `relative_path`); `ValueError` se o alvo for a raiz (sem pai).
3. `_find_dependents(root_module, target)` — varre toda a árvore procurando `Dependency` com `managed=False` cujo `(group_id, artifact_id)` bate com o do alvo. Módulos `managed=True` (entradas de BOM) não contam como "dependentes" — são a própria declaração de gerenciamento, não consumo real.
4. Se houver dependentes e `force=False` → `DependentModuleConflict(module_name, dependents=[nomes])`, nenhuma escrita acontece.
5. Caso contrário, aplica as escritas via `MavenPomWriter`: remove `<module>` do pai direto; se existir um módulo com `is_bom=True` (via `_find_bom_module`, busca recursiva) diferente do alvo, remove a entrada gerenciada dele; para cada dependente, remove a `<dependency>` correspondente.
6. Retorna `self.infer_structure(root_path)` — nunca constrói o `Project` atualizado manualmente, sempre re-lê o disco (consistente com a decisão de não ter manifesto próprio).

O valor gravado em `<module>` é calculado como `target.relative_path.relative_to(parent.relative_path)`, que reproduz exatamente o path relativo original usado no `<modules>` do pai (funciona também para módulos aninhados em subpastas).

## TUI (`ProjectDetailScreen`)

- Novo binding `r` → `action_remove_selected_module`, atuando sobre `self._selected_module` (atualizado em `on_tree_node_selected`).
- Usa `detect_adapter(project.root_path)` (mesmo serviço já usado no Dashboard/Import) para obter o adapter correto — a tela não guarda referência direta a `MavenAdapter`.
- Chama `remove_module(project, nome)` sem `force`; se `DependentModuleConflict`, monta uma mensagem com a lista de dependentes e abre `ConfirmModal` (`src/manager/screens/widgets/confirm_dialog.py`, novo — `ModalScreen[bool]` genérico reutilizável para futuras confirmações destrutivas); no callback, se confirmado, rechama com `force=True`.
- Após sucesso, `ProjectTree.refresh_project(project_atualizado)` (novo método, usa `Tree.reset()` + repopula recursivamente) reconstrói a árvore inteira a partir do `Project` re-inferido, e o painel de detalhes volta a mostrar o módulo raiz.
- Erros (`ValueError` — módulo raiz ou inexistente) são mostrados via `self.notify(..., severity="error")`, sem crashar a tela.

## Casos de borda tratados

- Módulo sem dependentes: remove direto, sem modal.
- Módulo com dependentes: modal → cancelar não altera nada; confirmar aplica `force=True`.
- Módulo raiz: erro claro, nenhuma escrita.
- Módulo inexistente: erro claro, nenhuma escrita.
- BOM módulo é o próprio alvo sendo removido: pula a etapa de remover entrada gerenciada dele mesmo (checagem `bom_module.relative_path != target.relative_path`).
