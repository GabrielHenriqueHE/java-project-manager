# Fase 9 — Marcar Diretório Registrado no Build — Requirements

## Contexto

Desde `phase-4-inferir-build`, um diretório customizado registrado via `build-helper-maven-plugin` (ex.: `src/main/proto`) é mesclado nas mesmas listas (`source_dirs`/`test_dirs`/`resource_dirs`/`test_resource_dirs`) que os diretórios de convenção padrão (`src/main/java`, etc.), então o dado já existe no modelo de domínio. A árvore do Painel [5] ESTRUTURA (`render_project_tree`) já exibe esses diretórios, mas sem nenhuma distinção visual entre "convenção padrão" e "registrado via build-helper" — fica indistinguível olhando só a árvore.

## Objetivo desta fatia

Distinguir visualmente, na árvore do Painel [5], um diretório que é convenção padrão de um que foi registrado explicitamente no build.

## Fora de escopo

Remoção de um nó qualquer da árvore, desregistrar um diretório do build, remoção de diretório não-vazio — ficam para fatias futuras já listadas em `specs/00-overview.md`.

## Critérios de aceite

- Dado um módulo cujo `source_dirs` contém apenas `src/main/java` (convenção padrão), quando a árvore é renderizada, então o nó aparece sem nenhuma marcação extra.
- Dado um módulo cujo `source_dirs` contém `src/main/java` e `src/main/proto` (este último registrado via build-helper), quando a árvore é renderizada, então `src/main/proto` aparece marcado (ex.: `[dim](build)[/]`) e `src/main/java` continua sem marcação.
- O mesmo vale para `test_dirs`/`resource_dirs`/`test_resource_dirs` frente aos seus respectivos defaults (`src/test/java`/`src/main/resources`/`src/test/resources`).
