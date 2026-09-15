# Fase 2 — Atualizar Metadados — Requirements

Terceira fatia de mutação real sobre [[03-gerenciamento-de-modulos]] e conclusão de [[02-metadados-do-projeto]]: implementar `update_metadata` de ponta a ponta (Maven), tanto no adapter quanto na TUI (Painel [2] METADADOS, que já anuncia "enter edita"). `update_dependency` fica para a fatia seguinte (`phase-2-update-dependency`).

## Escopo

**Dentro:**
- `MavenAdapter.update_metadata(project, module_name, metadata: ProjectMetadata) -> Project` funcional: atualiza `name`, `groupId`, `version`, `packaging`, `description` e a versão de Java (`java.version`, mapeada para as properties `maven.compiler.source`/`maven.compiler.target`) do pom do módulo indicado.
- Campo deixado em branco no formulário remove a tag correspondente do pom (ex.: limpar `description` remove `<description>`), exceto onde uma regra de obrigatoriedade se aplica (ver critérios de aceite).
- `groupId`/`version`: mesma regra de herança do `add_module` — se o valor informado for igual ao do pai (quando o módulo tem `<parent>`), a tag explícita é omitida/removida do pom (o módulo volta a herdar); se o módulo não tem `<parent>` (é a raiz), `groupId`/`version` são obrigatórios.
- Wiring na TUI: `MetadataPanel` (binding `enter`, já existente como `action_edit`) abre `MetadataFormScreen` pré-preenchido com os dados do módulo selecionado; confirmar aplica a mutação e atualiza os painéis.

**Fora (fatias seguintes ou fora do produto):**
- `update_dependency`.
- Renomear `artifactId`: exigiria renomear o diretório do módulo em disco, reescrever a entrada `<module>` no pom pai e qualquer `<artifactId>` em módulos dependentes — uma operação de "rename" com um raio de impacto bem maior que uma edição de metadados. `artifactId` é exibido como somente-leitura no formulário.
- Mudar `packaging` de um módulo que tem submódulos ou é o módulo BOM (`is_bom=True`) — mudar `packaging` para algo diferente de `pom` nesse caso quebraria a árvore de módulos ou o BOM sem nenhuma migração de conteúdo; a tentativa falha com erro claro e nenhuma escrita ocorre.
- Editar `properties` arbitrárias (apenas o par `maven.compiler.source`/`maven.compiler.target`, exposto como `java.version` no painel, é editável nesta fatia).

## User stories

- Como desenvolvedor Java, quero editar os metadados de um módulo (nome, groupId, versão, versão do Java, packaging, descrição) sem abrir o pom.xml manualmente.
- Como desenvolvedor Java, quero que limpar um campo opcional remova a tag correspondente do pom, mantendo o arquivo limpo em vez de gravar uma tag vazia.

## Critérios de aceite

- Editar `name`/`description` grava/atualiza a tag correspondente; limpar o campo remove a tag.
- Editar `groupId`/`version` de um módulo com `<parent>` para um valor igual ao do pai remove a tag explícita (herança implícita); para um valor diferente, grava a tag explícita.
- Editar `groupId`/`version` da raiz (sem `<parent>`) para um valor vazio falha com erro claro; nenhuma escrita ocorre.
- Editar `java.version` atualiza (ou cria) `<properties><maven.compiler.source>`/`<maven.compiler.target>`; limpar o campo remove as duas properties (e a seção `<properties>`, se ficar vazia — outras properties não relacionadas são preservadas).
- Tentar mudar `packaging` de um módulo com submódulos ou `is_bom=True` para um valor diferente de `pom` falha com erro claro; nenhuma escrita ocorre.
- Tentar editar um módulo com um `artifactId` diferente do original (violação da regra "somente-leitura") falha com erro claro — proteção também na camada do adapter, não só na TUI.
- Na TUI, cancelar o formulário não altera nada; confirmar aplica a mutação e atualiza os 5 painéis.

## Requisitos não funcionais

- Mesma garantia das fatias anteriores: o retorno é sempre uma re-inferência via `infer_structure` a partir do disco (ver [[05-inferencia-de-projeto-existente]]), nunca um `Project`/`Module` remontado em memória.
- A inserção de uma tag ausente (ex.: pom sem `<description>` ainda) respeita a ordem de elementos exigida pelo XSD do POM 4.0.0 (`modelVersion`, `parent`, `groupId`, `artifactId`, `version`, `packaging`, `name`, `description`, `properties`, `dependencyManagement`, `dependencies`, `modules`, ...) — um pom com uma tag inserida fora de ordem é inválido para o Maven, então não basta usar `append` no fim do elemento raiz.

## Dependências de outras features

- Depende de [[05-inferencia-de-projeto-existente]] (re-infere o estado após a mutação).
- Depende de [[02-metadados-do-projeto]] (campos e ordem definidos pela Fase 1 / `MetadataPanel`).

## Riscos / limitações conhecidas

- Assim como em `add_module`/`remove_module`, a tag de abertura `<project ...>` pode ser reformatada pelo lxml/libxml2 ao reescrever o arquivo.
- Não há suporte a desfazer (`undo`) — cada confirmação do formulário já grava no disco.
