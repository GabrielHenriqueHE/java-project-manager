# Fase 10 — Desregistrar Diretório do Build — Requirements

## Contexto

`register_directory_role` (Fase 4) registra um diretório customizado como fonte/recurso extra via `build-helper-maven-plugin`. Não existe o inverso: uma vez registrado, só dá pra remover a entrada editando o `pom.xml` manualmente. É a última peça pendente do ciclo escrita/leitura de diretórios customizados listado em `specs/00-overview.md` ("Fases futuras" #1).

## Objetivo desta fatia

Permitir desregistrar (remover a `<execution>` do `build-helper-maven-plugin`) um diretório já registrado, pela API do adapter e pela TUI. Não mexe no diretório em disco — só na entrada do build.

## Fora de escopo

Remoção de diretório não-vazio, remoção de um nó qualquer da árvore (continuam fora de escopo, já listados em `specs/00-overview.md`).

## Critérios de aceite

- Dado um módulo com `src/main/proto` registrado como `source`, quando `unregister_directory_role(project, module_name, "src/main/proto", "source")` é chamado, então a `<execution>` correspondente some do `pom.xml` e uma nova `infer_structure` não inclui mais `src/main/proto` em `source_dirs` (mesmo que a pasta continue existindo em disco).
- Dado um `(relative_path, role)` que não está registrado (ou um módulo sem `build-helper-maven-plugin` nenhum), quando desregistrado, então levanta `ValueError` — nenhuma escrita ocorre.
- Containers que ficam vazios após a remoção (`<executions>`, o `<plugin>` do build-helper, `<plugins>`, `<build>`) são removidos em cascata, no mesmo padrão já usado por `remove_managed_dependency`.
- Na TUI (Painel [5]), uma nova tecla abre um formulário (caminho + role) e desregistra; após confirmar, a árvore não mostra mais o sufixo `(build)` para aquele caminho.
