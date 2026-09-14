# Feature 03 — Gerenciamento de Módulos — Design

## Visão geral da solução

Toda mutação passa pela interface `BuildToolAdapter` (`add_module`, `remove_module`, `update_dependency`), nunca é feita diretamente pela TUI. O `MavenAdapter` é responsável por decidir *quais* arquivos tocar por operação: o pom pai para `<modules>`, o módulo BOM para `<dependencyManagement>`, e os poms dos módulos dependentes para suas `<dependency>`.

## Modelo de domínio envolvido

- `Module` (árvore via `submodules`), `Dependency` (`managed: bool` distingue BOM de dependência direta), `Project.managed_dependencies`.

## Interface de Adapter envolvida

- `remove_module(project, module_name, force=False)` — varre recursivamente `project.root_module` procurando `Dependency` cujo `group_id:artifact_id` corresponde ao módulo alvo. Se encontrar e `force=False`, levanta `DependentModuleConflict(module_name, dependents=[...])`. Com `force=True`, remove o `<module>` do pai, a entrada do BOM (se houver) e as `<dependency>` dos módulos dependentes.
- `add_module(project, module, parent_name=None)` — cria a pasta/estrutura do módulo (via [[04-estrutura-de-diretorios]]) e insere `<module>` no pom indicado (ou no pom raiz se `parent_name=None`).
- `update_dependency(project, module_name, dependency)` — se `dependency.managed=True`, escreve em `dependencyManagement` do módulo BOM; caso contrário, escreve como `<dependency>` direta no módulo indicado.

## Fluxo (remoção, caso mais complexo)

1. TUI chama `remove_module(project, "modulo-x", force=False)`.
2. Adapter varre a árvore, monta lista de dependentes.
3. Se lista não vazia → levanta `DependentModuleConflict` → TUI mostra modal de confirmação listando os dependentes → usuário confirma → TUI rechama com `force=True`.
4. Adapter aplica a remoção em todos os arquivos afetados numa sequência determinística (pom do módulo removido → pom pai → BOM → poms dependentes), re-roda `infer_structure` e retorna o `Project` atualizado.

## Impacto na camada Textual

- `screens/module_form.py` (criar/editar módulo), `screens/widgets/confirm_dialog.py` (`ConfirmModal(ModalScreen[bool])`, reutilizado para o fluxo de `DependentModuleConflict`).

## Casos de borda

- Módulo que é ao mesmo tempo BOM e tem dependentes.
- Remoção de um módulo que é `parent` de outros módulos (não apenas dependência) — tratado como erro distinto de `DependentModuleConflict` (estrutural, não de dependência), a especificar na fase que implementar isso.

## Alternativas consideradas e descartadas

- Aplicar mutações diretamente via manipulação de string/regex no `pom.xml` — descartado por fragilidade e risco de corromper XML; lxml com XPath é mais robusto e testável.
