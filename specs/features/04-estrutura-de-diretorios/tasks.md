# Feature 04 — Estrutura de Diretórios — Tasks

Coberto parcialmente pela **Fase 1** (modelo `DirectoryStructure`/`DirectoryNode` + inferência a partir da convenção Maven padrão) — ver `specs/phases/phase-1-fundacao/tasks.md` (tasks T4, T8).

**Criação de diretório em disco implementada** na Fase 4 (`specs/phases/phase-4-estrutura-diretorios/`): `BuildToolAdapter.add_directory` funcional de ponta a ponta no `MavenAdapter` (só I/O de filesystem, sem tocar em `pom.xml`) e na TUI (Painel [5] ESTRUTURA, checklist navegável com `j`/`k` + `enter` cria o item destacado).

**Diretório customizado (caminho livre) implementado** na segunda fatia da Fase 4 (`specs/phases/phase-4-diretorio-customizado/`): binding `n` no Painel [5] abre um formulário de caminho relativo livre, reaproveitando sem nenhuma mudança o `MavenAdapter.add_directory`/`MainScreen.add_directory` já existentes.

**Remoção de diretório vazio implementada** na terceira fatia da Fase 4 (`specs/phases/phase-4-remover-diretorio/`): novo `BuildToolAdapter.remove_directory` (só remove diretório vazio, nunca recursivo) e binding `d` no checklist do Painel [5].

**Registro no build implementado** na quarta fatia da Fase 4 (`specs/phases/phase-4-registrar-build/`): novo `BuildToolAdapter.register_directory_role`, escreve `<build><plugins>` com `org.codehaus.mojo:build-helper-maven-plugin` (goals `add-source`/`add-test-source`/`add-resource`/`add-test-resource` conforme o `role`) para o Maven reconhecer um diretório customizado como fonte/recurso extra. Binding `b` no Painel [5]. De brinde, corrigiu um bug pré-existente em `xml_utils.append_with_matching_indent` (container vazio ficava sem indentação) que estava latente desde `phase-2-add-module`.

Ainda fora de escopo: edição de `DirectoryNode.role` na visualização (o role só é escolhido no momento do registro no build, não fica associado ao diretório em memória entre sessões), remoção de diretório não-vazio, remoção de um nó qualquer da árvore (só os itens do checklist fixo são acionáveis), desregistrar um diretório já registrado no build, e ler de volta o `<build><plugins>` existente durante `infer_structure` para refletir no checklist/árvore — ficam para fatias futuras.
