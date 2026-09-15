# Feature 04 — Estrutura de Diretórios — Tasks

Coberto parcialmente pela **Fase 1** (modelo `DirectoryStructure`/`DirectoryNode` + inferência a partir da convenção Maven padrão) — ver `specs/phases/phase-1-fundacao/tasks.md` (tasks T4, T8).

**Criação de diretório em disco implementada** na Fase 4 (`specs/phases/phase-4-estrutura-diretorios/`): `BuildToolAdapter.add_directory` funcional de ponta a ponta no `MavenAdapter` (só I/O de filesystem, sem tocar em `pom.xml`) e na TUI (Painel [5] ESTRUTURA, checklist navegável com `j`/`k` + `enter` cria o item destacado).

**Diretório customizado (caminho livre) implementado** na segunda fatia da Fase 4 (`specs/phases/phase-4-diretorio-customizado/`): binding `n` no Painel [5] abre um formulário de caminho relativo livre, reaproveitando sem nenhuma mudança o `MavenAdapter.add_directory`/`MainScreen.add_directory` já existentes.

**Remoção de diretório vazio implementada** na terceira fatia da Fase 4 (`specs/phases/phase-4-remover-diretorio/`): novo `BuildToolAdapter.remove_directory` (só remove diretório vazio, nunca recursivo) e binding `d` no checklist do Painel [5].

Ainda fora de escopo: edição de `DirectoryNode.role`, remoção de diretório não-vazio, remoção de um nó qualquer da árvore (só os itens do checklist fixo são removíveis), e registro de diretórios não-padrão no `pom.xml` (ex.: `build-helper-maven-plugin`) — ficam para fatias futuras.
