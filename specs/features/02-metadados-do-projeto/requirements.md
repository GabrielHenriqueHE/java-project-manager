# Feature 02 — Metadados do Projeto

## Contexto/Problema

Cada projeto/módulo Java carrega metadados (groupId, artifactId, version, name, description, packaging) que hoje só podem ser vistos/editados abrindo o `pom.xml` manualmente. Erros de digitação ou inconsistência entre módulos (ex.: version divergente) são comuns.

## Objetivo

Permitir visualizar e, em fases futuras, editar os metadados de um projeto/módulo através da TUI, de forma agnóstica de build tool.

## Escopo

**Dentro (Fase 1):** visualização somente-leitura dos metadados inferidos de cada módulo.
**Fora (Fase 1, entra depois):** edição de metadados via TUI com escrita de volta no arquivo de build (`update_metadata` do adapter).

## User stories

- Como usuário, quero ver o groupId/artifactId/version/packaging de cada módulo do meu projeto sem abrir o pom.xml manualmente.
- Como usuário (fase futura), quero editar esses metadados pela TUI e ter o `pom.xml` correspondente atualizado automaticamente.

## Critérios de aceite

- Dado um projeto inferido, quando abro `ProjectDetailScreen`, então vejo os metadados de cada módulo selecionado (groupId, artifactId, version, packaging, name, description quando presentes).
- Dado um módulo sem `version` própria (herdada do parent), quando visualizado, então a ausência é indicada claramente (não confundida com string vazia).

## Requisitos não funcionais

- Campos ausentes no `pom.xml` (ex.: `description`) devem ser representados como ausentes (`None`), nunca inventados.
- O bag `properties` deve suportar chaves arbitrárias, para acomodar metadados não previstos no modelo Maven-cêntrico (ex.: propriedades customizadas do usuário).

## Dependências de outras features

- Depende de [[05-inferencia-de-projeto-existente]] para popular `ProjectMetadata`.
- Edição futura depende de [[03-gerenciamento-de-modulos]] (mesmo mecanismo de escrita/confirmação).

## Riscos / perguntas em aberto

- Metadados equivalentes em Gradle (`group`, `version` no `build.gradle`) têm formatos mais variados (Groovy DSL vs Kotlin DSL) — tratamento adiado para quando houver um `GradleAdapter`.
