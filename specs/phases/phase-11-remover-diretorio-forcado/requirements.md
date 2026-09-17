# Fase 11 — Remover Diretório Não-Vazio / Caminho Livre — Requirements

## Contexto

`remove_directory` (Fase 4, `phase-4-remover-diretorio`) só remove diretório vazio, e na TUI só os 8 itens do checklist fixo do Painel [5] são acionáveis — a árvore renderizada (`render_project_tree`) é texto estático, sem nós selecionáveis. Essas duas lacunas ficaram documentadas como a última pendência de [[04-estrutura-de-diretorios]] em `specs/00-overview.md`.

## Objetivo desta fatia

1. Permitir remover um diretório não-vazio (recursivamente), com confirmação explícita — mesmo padrão de risco/confirmação já usado por `remove_module`/`DependentModuleConflict`.
2. Permitir remover qualquer diretório do módulo por caminho livre (não só os 8 itens do checklist), simétrico ao que `phase-4-diretorio-customizado` já fez para criação (`n` + `DirectoryFormScreen`). Isso cobre "um nó qualquer da árvore" sem exigir tornar a árvore (hoje um `Static` de texto) navegável — o usuário digita o caminho, igual já faz para criar.

## Fora de escopo

Tornar a árvore do Painel [5] um widget navegável/selecionável (ex.: `Tree`) — mudança de UI maior, não necessária: o caminho livre já resolve o caso de uso de remover qualquer diretório.

## Critérios de aceite

- Dado um diretório vazio, quando removido (checklist `d` ou caminho livre), então remove direto, sem confirmação — comportamento inalterado da Fase 4.
- Dado um diretório com conteúdo, quando removido sem `force`, então a operação não altera nada e sinaliza que precisa de confirmação; a TUI mostra um `ConfirmModal` explicando que o conteúdo será apagado; confirmando, remove recursivamente (`force=True`); cancelando, nada muda.
- Dado um caminho que não é nenhum dos 8 itens do checklist (ex.: um diretório aninhado customizado), quando o usuário abre o novo formulário de caminho livre e digita esse caminho, então ele é removido (vazio direto, não-vazio com confirmação) — mesma lógica acima.
- Remover o próprio diretório-raiz do módulo continua bloqueado, mesmo com `force=True`.
