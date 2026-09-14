# Feature 01 — Gerenciamento de Projetos

## Contexto/Problema

Hoje, "abrir" um projeto Java significa navegar manualmente até a pasta e inspecionar arquivos. Não existe um lugar central que liste quais projetos o usuário costuma gerenciar, nem um jeito rápido de registrar um novo ou remover um antigo da lista de trabalho.

## Objetivo

Dar ao usuário um ponto de entrada único (dashboard) para ver, abrir, registrar e remover projetos Java conhecidos pela ferramenta.

## Escopo

**Dentro:**
- Listar projetos já registrados (nome, path, build tool).
- Registrar um projeto existente no disco (aponta para um path, a ferramenta detecta a build tool e infere a estrutura — ver [[05-inferencia-de-projeto-existente]]).
- Remover um projeto da lista de registrados (não apaga nada do disco — apenas "esquece" o projeto).
- Abrir um projeto registrado para ver seus detalhes.

**Fora (fases futuras):**
- Criar um projeto Java do zero (scaffold completo de um novo projeto multi-módulo) — depende de [[04-estrutura-de-diretorios]] e da capacidade de escrita do adapter, que na Fase 1 é só leitura.
- Clonar/baixar projetos de um repositório remoto.

## User stories

- Como usuário, quero ver uma lista dos projetos que já registrei, para retomar o trabalho rapidamente.
- Como usuário, quero apontar para uma pasta de um projeto Java existente e tê-lo registrado automaticamente, sem preencher metadados manualmente.
- Como usuário, quero remover um projeto da lista sem que isso afete os arquivos reais no disco.

## Critérios de aceite

- Dado que existem projetos registrados, quando abro a aplicação, então vejo todos eles listados no dashboard.
- Dado um path válido de projeto Maven, quando peço para registrar, então a build tool é detectada automaticamente e o projeto aparece na lista sem exigir input adicional de metadados.
- Dado um path inválido (não é projeto Java reconhecível), quando peço para registrar, então recebo uma mensagem de erro clara e nada é adicionado à lista.
- Dado um projeto registrado, quando peço para remover, então ele desaparece da lista e nenhum arquivo do projeto real é alterado.

## Requisitos não funcionais

- Remover um projeto da lista deve ser uma operação idempotente e não destrutiva (nunca toca no disco do projeto gerenciado).
- Registrar um projeto não deve duplicar entradas para o mesmo path.

## Dependências de outras features

- Depende de [[05-inferencia-de-projeto-existente]] para popular os dados exibidos ao registrar/abrir um projeto.

## Riscos / perguntas em aberto

- O que acontece se o path de um projeto registrado deixar de existir (pasta movida/apagada)? Tratamento definido na Fase 1: exibir o projeto como "indisponível" no dashboard, sem erro fatal.
