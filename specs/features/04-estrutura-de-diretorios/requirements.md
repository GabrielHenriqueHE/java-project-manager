# Feature 04 — Estrutura de Diretórios

## Contexto/Problema

Todo novo módulo/projeto Java precisa de uma estrutura de pastas padronizada (`src/main/java`, `src/test/java`, `src/main/resources`, etc. na convenção Maven). Criar isso manualmente para cada módulo novo é repetitivo, e projetos que fogem da convenção padrão (estrutura customizada) não têm um jeito fácil de declarar isso.

## Objetivo

Modelar a estrutura de diretórios de um módulo (convenção padrão ou customizada), permitir visualizá-la, e — em fases futuras — aplicá-la (criar as pastas reais) ao adicionar um módulo novo.

## Escopo

**Dentro (visão completa da feature):**
- Representar a estrutura de diretórios de um módulo (fonte, teste, recursos) de forma agnóstica de build tool.
- Suportar tanto a convenção padrão Maven quanto uma árvore customizada.
- Visualizar a estrutura inferida de um módulo existente.

**Fora (fases futuras):** editor visual de estrutura customizada; aplicação automática (criação de pastas em disco) ao definir uma nova estrutura.

## User stories

- Como usuário, quero ver a estrutura de diretórios de um módulo inferida automaticamente, para confirmar que segue a convenção esperada.
- Como usuário (fase futura), quero definir uma estrutura de diretórios customizada para um módulo novo e tê-la criada em disco automaticamente.

## Critérios de aceite

- Dado um módulo Maven que segue a convenção padrão, quando inferido, então `DirectoryStructure.convention == "maven-standard"` e os campos `source_dirs`/`test_dirs`/etc. batem com os defaults Maven.
- Dado um módulo com estrutura fora do padrão (ex.: `src/java` em vez de `src/main/java`), quando inferido, então `convention == "custom"` e os diretórios reais são refletidos, não os defaults.

## Requisitos não funcionais

- A representação deve ser serializável (Pydantic) para permitir persistência futura de "templates" de estrutura reutilizáveis entre projetos.

## Dependências de outras features

- Consumida por [[03-gerenciamento-de-modulos]] ao criar um módulo novo.
- Populada por [[05-inferencia-de-projeto-existente]].

## Riscos / perguntas em aberto

- Detecção de "convenção padrão vs. customizada" pode ter falsos negativos em projetos com pequenas variações (ex.: apenas `src/main/resources` ausente porque o módulo não tem recursos). Fase 1 considera esse caso ainda como `maven-standard` (ausência de uma pasta opcional não descaracteriza a convenção).
