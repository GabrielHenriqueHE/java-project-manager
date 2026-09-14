# Fase 3 — Reformulação da TUI ("mvnforge") — Requirements

## Contexto/Problema

O layout construído nas Fases 1-2 (Dashboard de projetos → tela de importação → tela de detalhe com árvore + painel de texto) não agradou ao usuário. Ele forneceu um design de referência detalhado (`specs/design/tui-layout.md`), extraído de um protótipo visual (project-buddy-cli.lovable.app), com um layout de **painel único, 3 colunas, 5 painéis numerados simultaneamente visíveis**, cabeçalho customizado e um rodapé com atalhos contextuais + modo comando.

## Objetivo

Substituir o fluxo de telas da Fase 1-2 por uma única tela (`MainScreen`) que implementa o layout descrito em `specs/design/tui-layout.md`, reaproveitando toda a camada de domínio/adapters/services já construída (nada muda em `models.py`, `adapters/`, `services/registry.py`, `services/adapters_registry.py`).

## Escopo

**Dentro:**
- Cabeçalho customizado (coordenada Maven + contadores).
- 5 painéis: Projetos, Metadados, Módulos, BOM+Dependências, Estrutura — cada um com header próprio (`[n] TITULO` + indicador contextual à direita) e `BINDINGS` declarados no próprio widget (não na `App`), para o `Footer` nativo do Textual mostrar atalhos contextuais por foco.
- Navegação entre painéis: teclas `1`-`5` e `tab`/`shift+tab` (nativo do Textual via ordem de foco).
- Seleção de projeto (Painel 1) atualiza todos os demais painéis.
- Seleção de módulo (Painel 3) atualiza Painel 2 (Metadados) e o "módulo ativo" inicial do Painel 5.
- `n` no Painel 1 abre o fluxo de importar/registrar projeto (reaproveita `ImportProjectScreen`).
- `d` no Painel 1 remove o projeto do registry (reaproveita `ProjectRegistry.remove`).
- `n` no Painel 3 abre `ModuleFormScreen` (reaproveitado da Fase 2) com o módulo selecionado como pai; `d` remove o módulo selecionado (reaproveita o fluxo `DependentModuleConflict` → `ConfirmModal` da Fase 2).
- Painel 5: checklist dos 8 diretórios convencionais (calculado por presença em disco, não só pelo `DirectoryStructure` do modelo) + árvore textual do projeto inteiro; `space` alterna qual módulo é o "ativo" para o checklist.
- Modo comando (`:`): substitui o footer por um `Input` com placeholder dinâmico; comando funcional `modulo <nome>` (atalho para `add_module` no painel/módulo ativo); qualquer outro comando reconhecido mas não implementado (`dependencia ...`) mostra aviso "ainda não implementado".
- Remover `DashboardScreen` e `ProjectDetailScreen` (e seus testes) — totalmente substituídos por `MainScreen`.

**Fora:**
- `update_metadata` e `update_dependency` reais (Painel 2 "enter edita" e Painel 4 "n"/"d" mostram apenas um aviso "ainda não implementado" — ver `specs/design/tui-layout.md`, seção de decisões).
- Edição do checklist de estrutura (marcar/desmarcar não cria/apaga diretórios).
- Paleta de cores/tema exata do protótipo (implementar uma aproximação razoável com os tokens de tema do Textual; não é pixel-perfect).

## Critérios de aceite

- Abrir a app mostra as 3 colunas com os 5 painéis, cabeçalho e rodapé, mesmo sem nenhum projeto registrado (estados vazios de cada painel).
- Selecionar um projeto no Painel 1 popula corretamente Metadados, Módulos, BOM+Dependências e Estrutura.
- Navegar entre módulos no Painel 3 atualiza o Painel 2 em tempo real.
- `n` e `d` funcionam nos Painéis 1 e 3 exatamente como funcionavam nas telas antigas (mesma lógica de negócio, nova apresentação).
- O rodapé muda os atalhos exibidos conforme o painel focado.
- `:` ativa o modo comando; `esc` cancela e volta ao footer normal; `modulo nome-x` cria de fato um módulo novo.
- `uv run pytest` verde cobrindo o novo `MainScreen` (testes antigos de `DashboardScreen`/`ProjectDetailScreen` removidos ou migrados).

## Dependências de outras features

Depende de toda a infraestrutura das Fases 1-2 ([[05-inferencia-de-projeto-existente]], [[01-gerenciamento-de-projetos]], [[03-gerenciamento-de-modulos]]) — nenhuma delas é alterada, apenas consumida por uma nova camada de apresentação.

## Riscos / limitações conhecidas

- Sem acesso ao protótipo Lovable real durante a implementação (apenas a descrição textual fornecida) — aproximações visuais (cores exatas, alinhamento pixel-a-pixel) podem divergir; o usuário deve validar visualmente rodando `uv run jpm`.
- Ver `specs/design/tui-layout.md` para as decisões explícitas tomadas em pontos não especificados pelo design original.
