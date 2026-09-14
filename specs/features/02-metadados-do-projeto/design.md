# Feature 02 — Metadados do Projeto — Design

## Visão geral da solução

`ProjectMetadata` (Pydantic) é um campo de `Module`, populado por `MavenPomParser` a partir das tags `<groupId>`, `<artifactId>`, `<version>`, `<name>`, `<description>`, `<packaging>` do `pom.xml`, com fallback para os valores do `parent` quando ausentes localmente (herança Maven).

## Modelo de domínio envolvido

- `ProjectMetadata` (`src/manager/models.py`).

## Interface de Adapter envolvida

- `BuildToolAdapter.infer_structure` (Fase 1, leitura).
- `BuildToolAdapter.update_metadata` (fase futura, escrita — stub `NotImplementedError` na Fase 1).

## Fluxo

1. `MavenPomParser.parse(pom_path)` lê o XML e monta um `ProjectMetadata` parcial (campos ausentes ficam `None`).
2. Se `groupId`/`version` estiverem ausentes no módulo mas houver `<parent>`, o parser resolve o valor herdado consultando o módulo pai já parseado (a resolução acontece em `MavenAdapter.infer_structure`, que tem visão da árvore completa, não no parser isolado).
3. `ProjectDetailScreen` exibe `MetadataPanel` com os dados do módulo selecionado na `ProjectTree`.

## Impacto na camada Textual

- `screens/widgets/metadata_panel.py` (leitura, Fase 1); edição fica para fase futura (modal reaproveitando o mesmo widget em modo editável).

## Casos de borda

- Módulo `packaging=pom` sem `description` — exibir campo como "—" na UI, não como string vazia.
- `properties` do Maven (`<properties>`) que não mapeiam para campos nomeados vão para o dict genérico `ProjectMetadata.properties`.

## Alternativas consideradas e descartadas

- Modelar metadados como `dict[str, str]` genérico sem campos nomeados — descartado porque perderia tipagem/autocomplete para os campos universais (groupId/artifactId/version/packaging), que existem em praticamente toda build tool relevante.
