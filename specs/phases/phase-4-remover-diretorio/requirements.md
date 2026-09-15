# Fase 4 — Remover Diretório — Requirements

Terceira fatia de [[04-estrutura-de-diretorios]], simétrica às duas anteriores (`phase-4-estrutura-diretorios` criou via checklist fixo, `phase-4-diretorio-customizado` criou via caminho livre): permite desfazer a criação de um item do checklist removendo-o do disco, limitado a diretórios **vazios**.

Escolhida como próximo passo em vez de "atribuir `role`" (tensão arquitetural: o produto nunca persiste estrutura própria — decisão 4 do overview — então não há onde lembrar uma escolha de role entre sessões) ou "registrar no `pom.xml`" (escopo maior, primeira escrita de `<build><plugins>`).

## Escopo

**Dentro:**
- `BuildToolAdapter.remove_directory(project, module_name, relative_path)` novo método na interface: remove `relative_path` (relativo à raiz do módulo) do disco **somente se estiver vazio**, e devolve o projeto re-inferido.
- `MavenAdapter.remove_directory`: mesma natureza de `add_directory` — só I/O de filesystem, nenhuma escrita de `pom.xml`.
- Validações: módulo precisa existir; `relative_path` não pode escapar do módulo (mesma proteção de `add_directory`); o diretório precisa existir; o diretório precisa estar vazio (nenhum arquivo nem subdiretório) — usa `Path.rmdir()` (que já falha nativamente em diretório não-vazio, mas validamos explicitamente antes para uma mensagem de erro clara em vez de propagar `OSError`).
- Wiring na TUI: Painel [5] (`StructurePanel`) ganha o binding `d` (mesma convenção de "remover" já usada nos Painéis 1/3) sobre o item do checklist atualmente destacado — remove se existir e estiver vazio.
- Sem modal de confirmação: como a operação só se aplica a diretórios vazios, não há dado (arquivo) em risco de ser perdido — mantém a simetria de interação direta já usada por `enter`/criar nesta mesma fatia anterior.

**Fora (fatias futuras ou fora do produto):**
- Remover diretório não-vazio (apagaria arquivos de código/recursos do usuário) — ação destrutiva de maior risco, fora de escopo. `MavenAdapter.remove_directory` falha com erro claro nesse caso, nunca remove recursivamente.
- Remover um diretório customizado criado via `phase-4-diretorio-customizado` (caminho livre) — a árvore renderizada no Painel [5] hoje é um `Static` de texto, sem nós selecionáveis; só os 8 itens do checklist fixo (`_CHECKLIST_DIRS`) são removíveis nesta fatia. Remover qualquer nó da árvore fica para uma fatia que torne a árvore navegável.
- Remover o próprio diretório do módulo (`relative_path` vazio/`.`) — barrado explicitamente, não é um caso de uso válido desta operação.

## User stories

- Como desenvolvedor Java, quero desfazer a criação de um diretório do checklist (ex.: criei por engano), sem sair da TUI para rodar `rmdir`.

## Critérios de aceite

- Destacar um item do checklist marcado como presente (`[x]`) e pressionar `d` remove o diretório vazio; o checklist volta a mostrar `[ ]` após o refresh.
- Tentar remover um item com conteúdo (arquivo ou subdiretório dentro) falha com erro claro; nada é removido.
- Tentar remover um item já ausente (`[ ]`) falha com erro claro (mensagem distinta de "não está vazio"), tratado como aviso informativo na TUI (mesmo padrão do "já existe" em `add_directory`).
- Tentar remover com um `relative_path` que escaparia do módulo falha com erro claro.

## Requisitos não funcionais

- Mesma garantia das fatias anteriores: o retorno é sempre uma re-inferência via `infer_structure`.
- A checagem de "vazio" roda antes de qualquer chamada a `rmdir()`, para que a mensagem de erro seja sempre a nossa (clara, em português), nunca um `OSError` cru do sistema operacional vazando pra UI.

## Dependências de outras features

- Depende de `phase-4-estrutura-diretorios` (reaproveita o mesmo checklist/estado de `StructurePanel`, e o mesmo padrão de path-traversal-guard de `add_directory`).

## Riscos / limitações conhecidas

- Mesma limitação já registrada nas fatias anteriores: remover a última pasta não-padrão sob `src/` pode fazer `detect_directory_structure` reclassificar o módulo de volta para `convention="maven-standard"` (ou vice-versa, dependendo do que restar) — comportamento pré-existente da função de inferência, não alterado aqui.
