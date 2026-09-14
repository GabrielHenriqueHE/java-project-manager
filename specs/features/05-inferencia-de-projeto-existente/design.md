# Feature 05 — Inferência de Projeto Existente — Design

## Visão geral da solução

`MavenAdapter.infer_structure(root_path)` orquestra dois componentes menores e testáveis isoladamente: `MavenPomParser` (lê um único `pom.xml` e extrai dados brutos) e a própria lógica de travessia recursiva do adapter (decide como montar a árvore `Module.submodules` a partir das tags `<modules>`).

## Modelo de domínio envolvido

- Todo o modelo: `Project`, `Module` (recursivo), `ProjectMetadata`, `Dependency`, `DirectoryStructure`, `BuildFile`.

## Interface de Adapter envolvida

- `detect(root_path) -> bool` — verifica se `root_path/pom.xml` existe e é um XML Maven válido (root element `<project>`).
- `infer_structure(root_path) -> Project` — método principal desta feature.

## Fluxo

1. `detect` confirma que é um projeto Maven.
2. `MavenPomParser.parse(root_path/pom.xml)` extrai metadata, dependências (diretas + `dependencyManagement`), e lista de `<module>` (paths relativos).
3. Para cada `<module>` listado, repete o parse recursivamente (`pom_path.parent / module_name / "pom.xml"`), construindo `Module.submodules`.
4. Após montar toda a árvore, uma passada de pós-processamento marca `is_bom=True` no(s) módulo(s) `packaging=pom` com `dependencyManagement` não vazio, e resolve dependências herdadas do `parent` quando `groupId`/`version` não estão declarados localmente.
5. `detect_directory_structure(module_path)` (ver [[04-estrutura-de-diretorios]]) roda para cada módulo folha (com código-fonte).
6. Resultado final: `Project(root_module=<árvore montada>, managed_dependencies=<espelho do BOM>)`.

## Impacto na camada Textual

- Nenhum diretamente — esta feature é a base de dados consumida por todas as telas.

## Casos de borda

- `pom.xml` sem `<modules>` (projeto single-module) — `Project.root_module` sem `submodules`, tratado normalmente.
- Import de BOM externo via `<dependencyManagement><dependencies><dependency><scope>import</scope>` apontando para um artefato de terceiros (não um módulo do próprio projeto) — registrado como `Dependency(managed=True)` no módulo importador, mas não vira um `Module` na árvore (não é um módulo do projeto).

## Alternativas consideradas e descartadas

- Resolver o projeto inteiro invocando `mvn help:effective-pom` como subprocesso (delegar a inferência ao próprio Maven) — descartado para a Fase 1 por adicionar uma dependência externa (Maven instalado e no PATH) e tempo de execução (spawna JVM); a leitura direta do XML é mais rápida e não exige nenhuma ferramenta externa instalada, alinhado ao objetivo de a aplicação funcionar de forma autocontida.
