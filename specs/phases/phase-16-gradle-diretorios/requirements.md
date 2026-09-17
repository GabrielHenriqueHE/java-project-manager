# Fase 16 — Gradle: Diretórios — Requirements

Segunda fatia de [[06-suporte-gradle]], primeira com mutação real (as demais 10 mutações da interface seguem como stub). Escolhida como próxima fatia por ser a única mutação que **não exige** editar `build.gradle(.kts)`: diretórios-padrão (`src/main/java` etc.) não precisam ser declarados no Gradle — são reconhecidos pela convenção do plugin `java`, exatamente como já são pelo Maven (`detect_directory_structure`, compartilhado desde a Fase 15). `add_directory`/`remove_directory` são, portanto, puramente filesystem + `infer_structure`, sem nenhum risco de escrita malformada em Groovy/Kotlin — o problema em aberto mais arriscado desta feature (editar código, não dados estruturados) fica para fatias futuras.

## Escopo desta fatia

**Dentro:**
- `GradleAdapter.add_directory(project, module_name, relative_path)` — cria o diretório em disco.
- `GradleAdapter.remove_directory(project, module_name, relative_path, force=False)` — remove o diretório do disco, com o mesmo guard de `DirectoryNotEmptyConflict` do Maven.
- Extração de `_find_module`/`_resolve_module_relative_path` (hoje privados em `MavenAdapter`, lógica pura sobre a árvore de domínio, sem nada específico de Maven) para `manager.adapters.common.lookup`, compartilhado pelos dois adapters — mesmo padrão de reaproveitamento já usado para `detect_directory_structure` na Fase 15.

**Fora (fatias futuras da feature):**
- `register_directory_role`/`unregister_directory_role` — no Gradle o mecanismo equivalente é `sourceSets{}`, que exige editar o build file; fora de escopo desta fatia e, conforme `specs/features/06-suporte-gradle/requirements.md`, fora de escopo da feature inteira por ora.
- Diretório customizado via caminho livre (binding `x`/`n` na TUI) — já funciona automaticamente nesta fatia, pois reaproveita `add_directory`/`remove_directory` sem nenhum código novo na TUI (ver design.md).
- Qualquer mutação que precise editar `build.gradle(.kts)` (`add_module`, `remove_module`, `update_dependency`, `update_metadata`, `remove_dependency`, `remove_direct_dependency`, `create_project`) — seguem stub.

## Critérios de aceite

- Dado um módulo Gradle sem `src/main/resources`, quando `add_directory(project, modulo, "src/main/resources")` é chamado, então o diretório é criado em disco e `infer_structure` volta a detectá-lo em `resource_dirs`.
- Dado um diretório vazio de um módulo Gradle, quando `remove_directory(project, modulo, caminho)` é chamado, então o diretório é removido do disco.
- Dado um diretório não-vazio, quando `remove_directory(..., force=False)` (default) é chamado, então levanta `DirectoryNotEmptyConflict` e nada é alterado; com `force=True`, remove recursivamente.
- Dado um `relative_path` que escaparia do diretório do módulo, ou um módulo inexistente, ou o próprio diretório-raiz do módulo, então levanta `ValueError` — mesmas mensagens/guards do `MavenAdapter`.
- Na TUI, com um projeto Gradle carregado, os bindings existentes do Painel [5] ESTRUTURA (`n`/`d`/`x`) funcionam sem nenhuma mudança de código de apresentação.

## Definição de pronto

`uv run pytest` verde, sem regressão no `MavenAdapter` (comportamento idêntico, só a origem de `_find_module`/`_resolve_module_relative_path` muda); `test_gradle_adapter_stubs.py` sem mais os dois casos de `add_directory`/`remove_directory` (não são mais stub).
