# Fase 1 — Fundação — Requirements

Escopo reduzido das 5 features para esta fase. Ver os `requirements.md` completos de cada feature para a visão de longo prazo.

## Req 1 — Gerenciamento de projetos ([[01-gerenciamento-de-projetos]])

- App lista projetos previamente registrados no `ProjectRegistry`.
- Fluxo de "Importar" funcional: aponta para um path, detecta a build tool, roda inferência real, registra.
- Remoção de projeto do registry funcional.
- **Fora desta fase**: criação de projeto do zero.

## Req 2 — Metadados ([[02-metadados-do-projeto]])

- Modelo `ProjectMetadata` completo.
- Tela de detalhe exibe (somente leitura) os metadados inferidos de cada módulo.
- **Fora desta fase**: edição de metadados.

## Req 3 — Módulos ([[03-gerenciamento-de-modulos]])

- Modelo `Module` suporta árvore de submódulos.
- `infer_structure` funcional (ver Req 5).
- `add_module`/`remove_module`/`update_dependency`/`update_metadata` existem na interface `BuildToolAdapter` mas ficam como stub (`NotImplementedError` documentado) nesta fase.

## Req 4 — Estrutura de diretórios ([[04-estrutura-de-diretorios]])

- `DirectoryStructure`/`DirectoryNode` existem no modelo.
- Populados pela inferência a partir da convenção Maven padrão.
- **Fora desta fase**: edição/aplicação de estrutura customizada.

## Req 5 — Inferência de projeto existente ([[05-inferencia-de-projeto-existente]]) — requisito âncora

- `MavenAdapter.infer_structure()` funcional contra um `pom.xml` multi-módulo de fixture, incluindo identificação correta do módulo BOM e resolução de dependências gerenciadas (`dependencyManagement`).
- Este é o critério de aceite mais importante da fase — sem ele, nenhuma tela consegue exibir dados reais.

## Critério de saída da Fase 1

- Todas as tasks de `tasks.md` desta fase concluídas.
- `uv run pytest` verde.
- `uv run jpm` abre o dashboard, permite importar a fixture de teste, e mostra a árvore de módulos corretamente em `ProjectDetailScreen`.
