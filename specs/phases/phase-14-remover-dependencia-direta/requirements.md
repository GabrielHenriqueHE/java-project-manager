# Fase 14 — Remover Dependência Direta na TUI — Requirements

## Contexto

A Fase 12 deu à TUI a capacidade de adicionar/editar uma dependência direta (`managed=False`) de qualquer módulo (Painel [4], `m`), mas removê-la ficou fora de escopo, adiado explicitamente em `specs/phases/phase-12-dependencia-direta/design.md`. O writer (`MavenPomWriter.remove_dependency`) já existe e é usado internamente por `remove_module` (para limpar dependências de módulos dependentes) — só não está exposto como operação de usuário nem tem método correspondente no `BuildToolAdapter`.

## Objetivo desta fatia

Remover uma dependência direta identificada por `groupId:artifactId` do módulo atualmente selecionado, pela TUI.

## Fora de escopo

Tornar a lista de diretas do Painel [4] um `ListView` navegável (mesma decisão já tomada na Fase 11 para diretórios: caminho/identificador livre resolve o caso de uso sem precisar de navegação por item, evitando a complexidade de alternar foco entre duas listas dentro do mesmo painel, já que `tab` está reservado para navegar entre painéis).

## Critérios de aceite

- Dado um módulo com uma dependência direta já registrada, quando o usuário informa `groupId`+`artifactId` dela num novo formulário do Painel [4] e confirma, então a `<dependency>` correspondente é removida de `<dependencies>` do módulo, e a seção de diretas do painel deixa de listá-la.
- Dado um `groupId:artifactId` que não é uma dependência direta do módulo selecionado (não existe, ou só existe como gerenciada), quando confirmado, então nada é removido e uma mensagem de erro clara aparece.
- Remover uma dependência direta nunca afeta `managed_dependencies` (BOM) do projeto nem dependências diretas de outros módulos.
