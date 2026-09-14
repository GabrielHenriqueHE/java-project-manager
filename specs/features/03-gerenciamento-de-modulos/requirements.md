# Feature 03 — Gerenciamento de Módulos

## Contexto/Problema

Esta é a dor original que motivou o projeto: adicionar um módulo Maven exige (a) criar a pasta/pom do módulo, (b) adicionar `<module>` no pom pai, (c) opcionalmente registrar a versão no BOM (`dependencyManagement`); remover um módulo exige o inverso, **e também** encontrar e limpar as `<dependency>` de todos os módulos que dependiam dele — passo que é fácil esquecer e causa build quebrado silenciosamente até o próximo `mvn install`.

## Objetivo

Automatizar adição, remoção e atualização de módulos garantindo que pom pai, BOM e módulos dependentes fiquem sempre consistentes entre si.

## Escopo

**Dentro (visão completa da feature, não necessariamente da Fase 1):**
- Adicionar um novo módulo a um projeto (cria estrutura de diretórios conforme [[04-estrutura-de-diretorios]], registra no pom pai).
- Remover um módulo, detectando e tratando módulos dependentes.
- Atualizar dependências de um módulo (incluindo entradas do BOM).

**Fora:** resolução de conflitos de versão complexos entre BOMs de terceiros (ex.: BOM importado de fora do projeto) — fora do escopo desta ferramenta, que gerencia apenas módulos do próprio projeto.

## User stories

- Como desenvolvedor Java, quero adicionar um novo módulo ao projeto e ter o pom pai atualizado automaticamente, sem editar XML à mão.
- Como desenvolvedor Java, quero remover um módulo e ser avisado se outros módulos dependem dele, para decidir conscientemente se quero remover essas dependências também.
- Como desenvolvedor Java, quero atualizar a versão de uma dependência gerenciada pelo BOM em um único lugar e ter certeza de que nenhum módulo ficou com versão divergente.

## Critérios de aceite

- Dado um projeto com N módulos, quando adiciono um módulo novo, então o pom pai passa a ter uma entrada `<module>` correspondente e o novo módulo aparece na próxima inferência (`infer_structure`).
- Dado um módulo M que é dependência de outros módulos D1, D2, quando peço para remover M sem confirmar, então recebo um erro (`DependentModuleConflict`) listando D1 e D2 e nada é alterado em disco.
- Dado o mesmo cenário, quando confirmo a remoção forçada, então M é removido do pom pai e as `<dependency>` correspondentes são removidas de D1 e D2.
- Dado um módulo que é o BOM do projeto, quando atualizo uma dependência gerenciada, então a entrada em `dependencyManagement` é alterada, não uma dependência direta.

## Requisitos não funcionais

- Toda mutação deve ser idempotente: reaplicar a mesma operação não deve gerar entradas duplicadas.
- Nenhuma mutação deve corromper partes do `pom.xml` não relacionadas à operação (preservar formatação/comentários fora do escopo da mudança).

## Dependências de outras features

- Depende de [[05-inferencia-de-projeto-existente]] (precisa saber o estado atual antes de mutar).
- Depende de [[04-estrutura-de-diretorios]] para criar a estrutura de pastas de um módulo novo.

## Riscos / perguntas em aberto

- Como identificar de forma confiável "o BOM do projeto" quando há mais de um módulo `packaging=pom` com `dependencyManagement`? Heurística inicial: `is_bom=True` no módulo cujo nome/artifactId contém convenção comum (`*-bom`, `*-dependencies`) OU que é explicitamente `import`ado via `<scope>import</scope>` pelos demais — a decidir em detalhe no design da fase que implementar mutação real.
