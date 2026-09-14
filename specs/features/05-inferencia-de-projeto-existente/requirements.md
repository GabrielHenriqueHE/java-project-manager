# Feature 05 — Inferência de Projeto Existente

## Contexto/Problema

A ferramenta não deve exigir que o usuário "recadastre" manualmente um projeto Java que já existe — ela precisa ler os arquivos de build reais (pom.xml, e futuramente build.gradle) e reconstruir o modelo de domínio automaticamente. Esta é a capacidade **âncora**: todas as outras features (metadados, módulos, estrutura de diretórios) dependem de conseguir inferir corretamente o estado atual antes de exibir ou mutar qualquer coisa.

## Objetivo

Dado o path raiz de um projeto Java, detectar automaticamente a build tool e montar um `Project` completo (árvore de módulos, metadados, dependências, estrutura de diretórios) sem exigir nenhum arquivo de configuração adicional da ferramenta.

## Escopo

**Dentro (Fase 1):**
- Detecção de projeto Maven (presença de `pom.xml` na raiz).
- Leitura recursiva da árvore de módulos (`<modules>`) a partir do pom raiz.
- Extração de metadados, dependências diretas e gerenciadas (BOM) por módulo.
- Identificação do módulo BOM (`is_bom`).
- Inferência de estrutura de diretórios (convenção Maven padrão vs. customizada).

**Fora (Fase 1):** suporte a Gradle (a interface `BuildToolAdapter` já prevê isso, mas a implementação `GradleAdapter` não é feita agora).

## User stories

- Como usuário, quero apontar a ferramenta para a raiz de um projeto Maven multi-módulo já existente e ver imediatamente todos os seus módulos, dependências e metadados, sem nenhuma configuração prévia.

## Critérios de aceite

- Dado um projeto Maven multi-módulo (pom pai + N módulos, incluindo um módulo BOM), quando `infer_structure(root_path)` é chamado, então o `Project` retornado tem exatamente os N+1 módulos esperados (pai + filhos), com o módulo BOM corretamente marcado `is_bom=True`.
- Dado um módulo que depende de outro módulo do mesmo projeto, quando inferido, então essa dependência aparece na lista `dependencies` do módulo consumidor com `group_id`/`artifact_id` batendo com o módulo provedor.
- Dado um path que não contém `pom.xml` na raiz, quando `detect(path)` é chamado, então retorna `False` (nenhuma exceção).
- Dado um `pom.xml` malformado, quando `infer_structure` é chamado, então uma exceção clara é levantada (não um crash genérico de parsing XML).

## Requisitos não funcionais

- A inferência não deve escrever nada em disco — é uma operação estritamente de leitura.
- A inferência deve ser determinística: rodá-la duas vezes seguidas sobre o mesmo projeto sem alterações produz o mesmo resultado.

## Dependências de outras features

- É pré-requisito de [[01-gerenciamento-de-projetos]], [[02-metadados-do-projeto]], [[03-gerenciamento-de-modulos]] e [[04-estrutura-de-diretorios]].

## Riscos / perguntas em aberto

- Projetos Maven com módulos referenciados por path relativo não convencional (`<module>../outro-lugar</module>`) — Fase 1 assume módulos dentro da árvore do projeto; casos fora da árvore ficam fora do escopo inicial.
