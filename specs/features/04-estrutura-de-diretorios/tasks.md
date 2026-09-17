# Feature 04 — Estrutura de Diretórios — Tasks

Coberto parcialmente pela **Fase 1** (modelo `DirectoryStructure`/`DirectoryNode` + inferência a partir da convenção Maven padrão) — ver `specs/phases/phase-1-fundacao/tasks.md` (tasks T4, T8).

**Criação de diretório em disco implementada** na Fase 4 (`specs/phases/phase-4-estrutura-diretorios/`): `BuildToolAdapter.add_directory` funcional de ponta a ponta no `MavenAdapter` (só I/O de filesystem, sem tocar em `pom.xml`) e na TUI (Painel [5] ESTRUTURA, checklist navegável com `j`/`k` + `enter` cria o item destacado).

**Diretório customizado (caminho livre) implementado** na segunda fatia da Fase 4 (`specs/phases/phase-4-diretorio-customizado/`): binding `n` no Painel [5] abre um formulário de caminho relativo livre, reaproveitando sem nenhuma mudança o `MavenAdapter.add_directory`/`MainScreen.add_directory` já existentes.

**Remoção de diretório vazio implementada** na terceira fatia da Fase 4 (`specs/phases/phase-4-remover-diretorio/`): novo `BuildToolAdapter.remove_directory` (só remove diretório vazio, nunca recursivo) e binding `d` no checklist do Painel [5].

**Registro no build implementado** na quarta fatia da Fase 4 (`specs/phases/phase-4-registrar-build/`): novo `BuildToolAdapter.register_directory_role`, escreve `<build><plugins>` com `org.codehaus.mojo:build-helper-maven-plugin` (goals `add-source`/`add-test-source`/`add-resource`/`add-test-resource` conforme o `role`) para o Maven reconhecer um diretório customizado como fonte/recurso extra. Binding `b` no Painel [5]. De brinde, corrigiu um bug pré-existente em `xml_utils.append_with_matching_indent` (container vazio ficava sem indentação) que estava latente desde `phase-2-add-module`.

**Leitura de volta do `<build><plugins>` implementada** na quinta fatia da Fase 4 (`specs/phases/phase-4-inferir-build/`): `MavenPomParser.parse()` lê as `<execution>` de `org.codehaus.mojo:build-helper-maven-plugin` já registradas e `MavenAdapter._build_module` mescla os diretórios encontrados (que ainda existam em disco) nas listas `source_dirs`/`test_dirs`/`resource_dirs`/`test_resource_dirs` de `DirectoryStructure`, fechando o ciclo escrita (`phase-4-registrar-build`) → leitura (`infer_structure`). As constantes/mapeamentos do plugin foram extraídas para `src/manager/adapters/maven/build_helper.py`, compartilhadas entre `writer.py` (escrita) e `parser.py` (leitura).

**Marcação visual de diretório registrado implementada** na sexta fatia da Fase 4/nona fase geral (`specs/phases/phase-9-marcar-diretorio-registrado/`): a árvore do Painel [5] (`render_project_tree`) sufixa `[dim](build)[/]` em qualquer diretório de `source_dirs`/`test_dirs`/`resource_dirs`/`test_resource_dirs` que não seja o caminho de convenção padrão da sua lista, sem mudança de modelo de domínio nem acoplamento a `manager.adapters.maven` (compara contra os próprios defaults de `DirectoryStructure`).

Ainda fora de escopo: remoção de diretório não-vazio, remoção de um nó qualquer da árvore (só os itens do checklist fixo são acionáveis), e desregistrar um diretório já registrado no build — ficam para fatias futuras.
