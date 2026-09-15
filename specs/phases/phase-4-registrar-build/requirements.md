# Fase 4 — Registrar Diretório no Build — Requirements

Quarta fatia de [[04-estrutura-de-diretorios]]: as três fatias anteriores criam/removem pastas em disco, mas o Maven só reconhece automaticamente as 4 pastas convencionais (`src/main/java`, `src/test/java`, `src/main/resources`, `src/test/resources`). Um diretório customizado (ex.: `src/main/proto`) criado nas fatias anteriores existe no disco mas o Maven o ignora na build — para virar fonte/recurso de verdade, precisa ser registrado via plugin no `pom.xml`. Esta fatia fecha essa lacuna usando `org.codehaus.mojo:build-helper-maven-plugin`, a forma padrão da comunidade Maven de adicionar diretórios extra de fonte/recurso sem reestruturar o projeto.

Escolhida em vez de "atribuir `role`" (mesma tensão arquitetural já registrada: sem manifesto próprio, não há onde lembrar uma escolha de role entre sessões — **mas nesta fatia o "role" escolhido pelo usuário é gravado diretamente no `pom.xml`, que já é a fonte de verdade real do projeto; não é um manifesto proprietário da ferramenta, então não reabre a decisão 4**) e em vez de "remover diretório não-vazio/nó da árvore" (mais arriscado: apaga arquivos de verdade, e exigiria tornar a árvore navegável).

## Escopo

**Dentro:**
- `BuildToolAdapter.register_directory_role(project, module_name, relative_path, role)` novo método na interface: registra `relative_path` como fonte/recurso extra do `role` indicado no arquivo de build do módulo. `role` é um dos 4 valores utilizáveis de `DirectoryRole` (`source`, `test-source`, `resource`, `test-resource` — `other` é inválido para este método, não corresponde a nenhum goal do plugin).
- `MavenAdapter.register_directory_role`: escreve/atualiza `<build><plugins><plugin>` com `groupId=org.codehaus.mojo`, `artifactId=build-helper-maven-plugin`, reaproveitando o plugin existente se o módulo já tiver um registrado (não duplica o bloco `<plugin>` a cada chamada), e adiciona uma `<execution>` com o goal correspondente ao `role`:
  - `source` → goal `add-source`, fase `generate-sources`, `<configuration><sources><source>`.
  - `test-source` → goal `add-test-source`, fase `generate-test-sources`, `<configuration><sources><source>`.
  - `resource` → goal `add-resource`, fase `generate-resources`, `<configuration><resources><resource><directory>`.
  - `test-resource` → goal `add-test-resource`, fase `generate-test-resources`, mesma forma de `resource`.
- Idempotente: chamar de novo com o mesmo `(role, relative_path)` não duplica a `<execution>` (identificada por um `<id>` determinístico, ex.: `add-source-src-main-proto`) — nenhuma escrita ocorre na segunda chamada.
- Validação: o diretório precisa já existir em disco (criado antes via `add_directory`/formulário de caminho livre) — este método só mexe no `pom.xml`, nunca cria pastas.
- Wiring na TUI: Painel [5] ganha o binding `b` (mnemônico "build"), que abre um formulário com dois campos — caminho e `role` — e chama a operação.

**Fora (fatias futuras ou fora do produto):**
- Desregistrar (remover a `<execution>`/`<plugin>` do build) — fora de escopo; ação de remoção fica para uma fatia futura simétrica.
- Inferir automaticamente, ao rodar `infer_structure`, que um diretório já está registrado no build (ex.: popular `DirectoryStructure` a partir do `<build><plugins>` existente) — esta fatia só escreve; ler de volta essas execuções para refletir no checklist/árvore é trabalho futuro.
- Suportar outros plugins/mecanismos de registro de fonte além de `build-helper-maven-plugin` (ex.: plugins de protobuf, plugins de `webapp`) — apenas o caso genérico "pasta extra de source/resource" é coberto.
- Validar que o `pom.xml` já declara o plugin com uma versão compatível, ou resolver a versão mais recente do plugin dinamicamente — a versão gravada é fixa (`3.6.0`), sem chamada de rede.

## User stories

- Como desenvolvedor Java, quero que uma pasta customizada que criei (ex.: `src/main/proto`) seja reconhecida pelo Maven como fonte extra, sem editar `pom.xml` à mão para configurar o `build-helper-maven-plugin`.

## Critérios de aceite

- Registrar `src/main/proto` como `source` num módulo sem `<build>` ainda cria toda a estrutura (`<build><plugins><plugin>...<executions><execution>...`) na posição correta do pom.
- Registrar uma segunda pasta/role no mesmo módulo reaproveita o `<plugin>` já existente, só adiciona uma nova `<execution>`.
- Registrar a mesma pasta/role duas vezes não duplica a `<execution>` nem reescreve o arquivo desnecessariamente.
- Tentar registrar um diretório que não existe em disco falha com erro claro; nenhuma escrita ocorre.
- Tentar registrar com `role="other"` (ou qualquer valor fora dos 4 válidos) falha com erro claro.

## Requisitos não funcionais

- Mesma garantia das fatias anteriores: o retorno é sempre uma re-inferência via `infer_structure`.
- Reaproveita `xml_utils.ensure_child_in_order`/`append_with_matching_indent` (de `phase-2-update-metadata`/`phase-2-update-dependency`) para inserir `<build>`/`<plugins>`/`<executions>` respeitando indentação existente, e o mesmo padrão de "construir elemento desanexado + `etree.indent(el, level=depth)`" já validado em `_append_dependency_element` para a subárvore aninhada da `<execution>`.

## Dependências de outras features

- Depende de `phase-4-estrutura-diretorios`/`phase-4-diretorio-customizado` (o diretório precisa existir antes de ser registrado).
- Depende de [[05-inferencia-de-projeto-existente]].

## Riscos / limitações conhecidas

- A versão do `build-helper-maven-plugin` (`3.6.0`) é fixa no código; se o usuário já tiver uma versão diferente declarada manualmente no pom, esta fatia reaproveita o `<plugin>` existente **sem tocar na tag `<version>`** (só adiciona a `<execution>`), evitando downgrade/upgrade silencioso.
- Como não há leitura de volta (ver "Fora"), o checklist/árvore do Painel [5] não mostra visualmente que uma pasta já está registrada no build — só o `pom.xml` reflete isso até uma fatia futura de leitura.
