# Fase 2 — Adicionar Módulo — Requirements

Segunda fatia de mutação real sobre [[03-gerenciamento-de-modulos]]: implementar `add_module` de ponta a ponta (Maven), tanto no adapter quanto na TUI. `update_dependency`/`update_metadata` ficam para fatias seguintes.

## Escopo

**Dentro:**
- `MavenAdapter.add_module(project, module, parent_name=None)` funcional: cria a pasta e o `pom.xml` do módulo (com `<parent>` apontando para o pai), a estrutura de diretórios padrão (`src/main/java`, `src/test/java`, `src/main/resources`, `src/test/resources`), e registra `<module>` no pom do pai.
- `parent_name=None` usa o módulo raiz como pai; caso contrário busca o módulo pelo nome.
- Validações: pai precisa ter `packaging=pom`; nome do novo módulo não pode colidir com um módulo já existente; o diretório de destino não pode já existir; o pom do pai precisa já ter uma seção `<modules>` (ver limitação abaixo).
- `groupId`/`version` só são escritos explicitamente no novo pom quando diferem do pai — caso contrário, o módulo herda por convenção Maven (`<parent>`), evitando poluir o pom com dados redundantes.
- Dependências iniciais (`module.dependencies`) são escritas no novo pom, particionadas entre `<dependencies>` (diretas) e `<dependencyManagement>` (quando `managed=True`).
- Wiring na TUI: `ProjectDetailScreen` ganha o binding `a`, que abre `ModuleFormScreen` (artifactId, groupId, version, packaging, name, description) usando o módulo selecionado na árvore como pai.

**Fora (fatias seguintes):**
- `update_dependency`, `update_metadata`.
- Criar a seção `<modules>` do zero quando o pom pai ainda não tiver nenhuma (hoje isso falha com um erro claro em vez de tentar inserir a seção — decisão para não arriscar uma inserção mal posicionada num pom sem esse bloco).
- Editor de dependências iniciais pela TUI (o form não expõe esse campo ainda; só a API do adapter e os testes exercitam isso).
- Inferir/gerar código Java inicial (ex.: uma classe placeholder) — apenas a estrutura de diretórios vazia é criada.

## User stories

- Como desenvolvedor Java, quero criar um novo módulo dentro do projeto e ter o pom pai atualizado automaticamente, sem editar XML à mão nem criar a estrutura de pastas manualmente.

## Critérios de aceite

- Criar um módulo sob a raiz registra `<module>` no pom raiz e cria as 4 pastas padrão vazias.
- Criar um módulo sem informar groupId/version faz o módulo herdar do pai (nenhuma tag `<groupId>`/`<version>` extra é escrita no filho).
- Informar um groupId ou version diferente do pai escreve essas tags explicitamente no filho.
- Tentar usar como pai um módulo com `packaging` diferente de `pom` falha com erro claro.
- Tentar usar um nome já existente no projeto falha com erro claro.
- Tentar usar um pai cujo pom não tem `<modules>` falha com erro claro (nenhum arquivo é alterado).
- Na TUI, cancelar o formulário não cria nada; confirmar cria o módulo e atualiza a árvore exibida.

## Requisitos não funcionais

- A ordem das escritas garante que, se `create_pom` falhar, o pom do pai nunca chega a referenciar um módulo inexistente (a entrada `<module>` só é escrita depois que o diretório/pom do filho já existem no disco).
- Como em [[05-inferencia-de-projeto-existente]], o retorno é sempre uma re-inferência a partir do disco — nunca um `Project` montado manualmente em memória.

## Dependências de outras features

- Depende de [[05-inferencia-de-projeto-existente]] (usa `infer_structure` para devolver o estado pós-criação e para localizar o pai/validar nomes).
- Depende de [[04-estrutura-de-diretorios]] (usa `Module.directory_structure` — por padrão o `maven-standard` — para decidir quais pastas criar).

## Riscos / limitações conhecidas

- Assim como em `remove_module`, a tag de abertura `<project ...>` é sempre serializada em uma única linha pelo lxml/libxml2, mesmo que o pom pai original a tivesse em múltiplas linhas.
