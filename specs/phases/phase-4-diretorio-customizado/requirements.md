# Fase 4 — Diretório Customizado — Requirements

Segunda fatia de [[04-estrutura-de-diretorios]], em cima de `phase-4-estrutura-diretorios` (que só ativou o checklist fixo de 8 itens). Esta fatia fecha a lacuna original da feature ("projetos que fogem da convenção padrão não têm um jeito fácil de declarar isso"): permitir digitar **qualquer** caminho relativo, não só os itens pré-listados.

## Escopo

**Dentro:**
- Painel [5] ESTRUTURA ganha o binding `n` (mesma convenção de "criar novo" já usada nos Painéis 1/3/4), que abre um formulário simples com um único campo — caminho relativo (ex.: `src/main/proto`, `docs/adr`) — para o módulo atualmente ativo no painel.
- Reaproveita **sem nenhuma mudança** a camada de domínio/adapter: o mesmo `MavenAdapter.add_directory` e o mesmo `MainScreen.add_directory` da fatia anterior já cobrem "criar uma pasta relativa a um módulo, validando duplicidade e path traversal" — o único gap era a UI só oferecer 8 caminhos fixos.

**Fora (fatias futuras ou fora do produto):**
- Atribuir `DirectoryRole` ao diretório customizado — como o produto nunca persiste estrutura própria (decisão arquitetural 4 em [[00-overview]]: tudo é re-inferido do disco via `infer_structure`), não há hoje onde guardar "o usuário classificou `src/main/proto` como `source`" para a próxima inferência lembrar. Resolver isso exigiria ou um manifesto próprio (rejeitado pela decisão 4) ou inferir `role` por heurística de nome — nenhum dos dois está nesta fatia.
- Validação de que o caminho "faz sentido" para a build tool (ex.: avisar que uma pasta fora de `src/` não é reconhecida pelo Maven sem plugin extra) — o formulário aceita qualquer caminho relativo válido, sem julgamento sobre convenções.

## User stories

- Como desenvolvedor Java, quero criar uma pasta customizada (fora dos 8 itens do checklist padrão) para o módulo ativo, digitando o caminho relativo, sem sair da TUI.

## Critérios de aceite

- No Painel [5], pressionar `n` abre um formulário com um campo de caminho; confirmar com um caminho válido cria a pasta (via `MavenAdapter.add_directory`, mesmas validações de duplicidade/traversal já cobertas pelos testes da fatia anterior) e atualiza o checklist/árvore.
- Confirmar com o campo vazio não faz nada e mostra feedback no próprio formulário (mesmo padrão de `ModuleFormScreen`/`DependencyFormScreen`).
- Cancelar não altera nada em disco.
- Digitar um caminho que já existe ou que escapa do módulo reaproveita o mesmo tratamento de erro/aviso já existente em `MainScreen.add_directory`.

## Requisitos não funcionais

- Nenhuma mudança em `src/manager/adapters/` — esta fatia é só uma nova porta de entrada de UI para uma capacidade já implementada e testada.

## Dependências de outras features

- Depende inteiramente de `phase-4-estrutura-diretorios` (reaproveita `MavenAdapter.add_directory`/`MainScreen.add_directory` sem alteração).

## Riscos / limitações conhecidas

- Mesma limitação já registrada na fatia anterior: criar uma pasta não-padrão sob `src/` reclassifica o módulo inteiro como `convention="custom"` na próxima inferência (comportamento pré-existente de `detect_directory_structure`, não alterado aqui).
