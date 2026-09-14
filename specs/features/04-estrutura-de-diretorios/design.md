# Feature 04 — Estrutura de Diretórios — Design

## Visão geral da solução

`DirectoryStructure` guarda listas nomeadas de diretórios (source/test/resource) mais um campo `convention` que indica se o módulo segue o padrão Maven ou uma estrutura livre. Uma `DirectoryNode` recursiva opcional (`tree`) permite renderizar a árvore completa na TUI quando necessário, sem forçar todo consumidor a lidar com uma árvore genérica.

## Modelo de domínio envolvido

- `DirectoryNode` (recursivo: `name`, `role`, `children`).
- `DirectoryStructure` (`convention`, `source_dirs`, `test_dirs`, `resource_dirs`, `test_resource_dirs`, `tree` opcional).

## Interface de Adapter envolvida

- `infer_structure` popula `DirectoryStructure` por módulo, verificando a existência das pastas convencionais (`src/main/java`, `src/test/java`, `src/main/resources`, `src/test/resources`) relativas ao `pom.xml` do módulo.
- Aplicação de estrutura customizada (criação de pastas) fica para fase futura, não faz parte de nenhum método da interface na Fase 1.

## Fluxo

1. `MavenAdapter.infer_structure` chama uma função auxiliar `detect_directory_structure(module_path)` para cada módulo.
2. Se todas as pastas padrão presentes (ou ausentes apenas por não terem conteúdo aplicável, ex. sem resources) → `convention="maven-standard"`.
3. Caso contrário → `convention="custom"`, e os campos de diretório refletem o que foi encontrado na varredura real (não os defaults).

## Impacto na camada Textual

- `screens/directory_structure.py` (visualização, Fase 1; edição em fase futura).

## Casos de borda

- Módulo `packaging=pom` (agregador puro, sem código) — `DirectoryStructure` pode não ter nenhuma pasta de fonte; isso não é erro, é esperado para módulos agregadores/BOM.

## Alternativas consideradas e descartadas

- Modelar a estrutura só como árvore genérica (`DirectoryNode` sempre, sem campos nomeados) — descartado porque perde a semântica direta de "onde está o source Java" que a maioria das operações (ex.: criar um módulo novo) precisa consultar diretamente.
