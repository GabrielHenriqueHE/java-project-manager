# Fase 4 — Registrar Diretório no Build — Tasks

- [x] **T1** — `BuildToolAdapter.register_directory_role` (novo método abstrato em `src/manager/adapters/base.py`).
- [x] **T2** — `MavenPomWriter.register_directory_role` (`_find_plugin_element`, `_find_execution_element`, construção de `<build><plugins><plugin><executions><execution>` idempotente).
- [x] **T3** — `MavenAdapter.register_directory_role` (validação de módulo/role/diretório existente, re-inferência).
- [x] **T4** — Testes isolados (`tests/test_maven_adapter_register_directory_role.py`, 8 casos) usando cópia da fixture em `tmp_path` — cobrindo: registra `source` novo (cria `<build>` do zero, com checagem de indentação), registra `resource` (estrutura `<resources><resource><directory>`), segunda pasta/role reaproveita o mesmo `<plugin>`, idempotência (mesma pasta/role duas vezes não duplica), erro em diretório inexistente, erro em role inválido, erro em módulo inexistente, fixture versionada intocada.
- [x] **T5** — `BuildSourceFormScreen` (`src/manager/screens/widgets/build_source_form.py`).
- [x] **T6** — Wiring: `StructurePanel` binding `b` → `action_register_build_source`; `MainScreen.register_build_source` novo.
- [x] **T7** — Testes de TUI em `tests/test_main_screen.py` (3 casos novos): registrar via formulário escreve no pom, role inválido mantém o formulário aberto com feedback, cancelar não altera nada.
- [x] **T8** — Atualizar `specs/features/04-estrutura-de-diretorios/tasks.md` e `specs/00-overview.md` para refletir a quarta fatia da Fase 4.

## Bug encontrado e corrigido durante a implementação

`xml_utils.append_with_matching_indent` tinha um bug pré-existente (desde `phase-2-add-module`) no caminho "container vazio": só setava `new_child.tail`, nunca `container.text` — então o primeiro filho de um container recém-criado (`<plugins>`, `<executions>`, etc.) ficava colado na tag de abertura do pai (`<build><plugins>`) em vez de indentado numa linha própria. Ficou invisível nas fatias anteriores porque `create_pom` sempre reformata a árvore inteira no final (`etree.indent(tree)`), mascarando o problema; só apareceu de forma óbvia aqui por causa do aninhamento profundo (`build>plugins>plugin>executions>execution`, 3 containers vazios em sequência numa edição pontual, sem reformatação global). Corrigido calculando a indentação pela profundidade real do container (`sum(1 for _ in container.iterancestors())`) e setando `container.text` também, não só `new_child.tail`. Testes de regressão dedicados em `tests/test_xml_utils.py`.

## Definição de pronto

`uv run pytest` verde; registrar um diretório customizado no build funcional via API do adapter e via TUI; nenhuma fixture versionada foi mutada pelos testes.
