# Fase 4 — Inferir Diretórios Registrados no Build — Requirements

Quinta fatia de [[04-estrutura-de-diretorios]]: `phase-4-registrar-build` grava `<build><plugins><org.codehaus.mojo:build-helper-maven-plugin>` no `pom.xml` para que o Maven reconheça um diretório customizado como fonte/recurso extra, mas nunca lê essas execuções de volta — `infer_structure` as ignora completamente. Resultado: reabrir um projeto (ou simplesmente rodar `infer_structure` de novo após um `register_directory_role`) não reflete, em memória, que aquele diretório já está registrado. Esta fatia fecha o ciclo escrita/leitura: `infer_structure` volta a ler `<build><plugins>` e inclui os diretórios já registrados nas listas por papel (`role`) do módulo.

Escolhida como próxima fatia (em vez de "refletir `role` no checklist visual" ou "desregistrar diretório") porque é pré-requisito das duas: sem os dados disponíveis no modelo de domínio após `infer_structure`, não há o que exibir no checklist nem o que remover de forma consistente.

## Escopo

**Dentro:**
- `MavenPomParser.parse()` passa a ler `<build><plugins><plugin>` cujo `groupId`/`artifactId` batem com `org.codehaus.mojo:build-helper-maven-plugin` e, para cada `<execution>`, extrai o `goal` (mapeado de volta para o `role` correspondente — inverso do mapeamento já usado em `MavenPomWriter.register_directory_role`) e o(s) caminho(s) configurado(s) (`<configuration><sources><source>` para `source`/`test-source`, `<configuration><resources><resource><directory>` para `resource`/`test-resource`).
- `ParsedPom` ganha um novo campo, `registered_directories: list[tuple[str, DirectoryRole]]`, com os pares `(caminho relativo, role)` encontrados (lista vazia se não houver `<build><plugins>` ou nenhum plugin/execução reconhecível).
- `MavenAdapter._build_module` passa a mesclar esses pares na `DirectoryStructure` do módulo: cada `(caminho, role)` cujo diretório ainda exista em disco é incluído na lista correspondente (`source_dirs`, `test_dirs`, `resource_dirs` ou `test_resource_dirs`), sem duplicar entradas já presentes (ex.: convenção padrão já detectada) e independente da `convention` já calculada (`maven-standard` ou `custom`).
- As constantes/mapeamentos do plugin (`groupId`, `artifactId`, goal↔role) usados tanto por `register_directory_role` (escrita) quanto por esta fatia (leitura) passam a viver num único módulo compartilhado (`src/manager/adapters/maven/build_helper.py`), eliminando duplicação e o risco de os dois lados divergirem.

**Fora (fatias futuras ou fora do produto):**
- Popular `DirectoryNode.role` na árvore (`DirectoryStructure.tree`) para refletir visualmente no checklist/árvore do Painel [5] — esta fatia só disponibiliza o dado no modelo de domínio (`source_dirs`/`test_dirs`/`resource_dirs`/`test_resource_dirs`); a apresentação na TUI é a fatia seguinte.
- Desregistrar um diretório do build (remover a `<execution>`/`<plugin>`) — fatia futura simétrica a `register_directory_role`.
- Reconhecer outros plugins/mecanismos de registro de fonte além de `build-helper-maven-plugin` (ex.: plugins de protobuf) — mesma limitação já assumida em `phase-4-registrar-build`.
- Validar ou normalizar o `<phase>`/`<id>` da `<execution>` — a leitura confia apenas no `<goal>` e na `<configuration>` para reconstruir `(caminho, role)`; qualquer inconsistência entre `<id>`/`<phase>` e o `<goal>` real (ex.: pom editado manualmente) é ignorada.

## User stories

- Como desenvolvedor Java, quero que ao reabrir um projeto (ou repetir uma inferência) a ferramenta continue sabendo que `src/main/proto` já está registrado como fonte extra, sem precisar registrar de novo nem perder essa informação da memória da aplicação.

## Critérios de aceite

- Um módulo cujo `pom.xml` já tem uma `<execution>` de `add-source` apontando para `src/main/proto` (e o diretório existe em disco) tem `"src/main/proto"` em `directory_structure.source_dirs` após `infer_structure`.
- O mesmo vale para `test-source` → `test_dirs`, `resource`/`test-resource` → `resource_dirs`/`test_resource_dirs`, usando `<configuration><resources><resource><directory>`.
- Um diretório registrado no `pom.xml` mas removido do disco manualmente (fora da ferramenta) **não** aparece nas listas — mesma regra já aplicada à detecção de convenção padrão (só lista o que existe de fato).
- Um módulo sem `<build>`, ou com `<build><plugins>` mas sem `build-helper-maven-plugin`, ou com outros plugins não relacionados, continua inferindo normalmente (`registered_directories` vazio, nenhuma mudança de comportamento).
- Rodar `register_directory_role` seguido de `infer_structure` (já é o retorno padrão de `register_directory_role`) reflete o diretório recém-registrado na lista correspondente — fecha o ciclo escrita→leitura na mesma chamada.
- `infer_structure` continua determinístico (duas chamadas seguidas produzem o mesmo `Project`).

## Requisitos não funcionais

- Nenhuma escrita em disco — fatia estritamente de leitura, sem novo método na interface `BuildToolAdapter`.
- Reaproveita o parsing de namespace (`namespace_of`) e o padrão de busca linear (`findall`/`find`) já usados no restante de `parser.py`.

## Dependências de outras features

- Depende de `phase-4-registrar-build` (formato de `<build><plugins>` que esta fatia lê).
- Depende de [[05-inferencia-de-projeto-existente]].

## Riscos / limitações conhecidas

- Se o usuário editar `<execution><goal>` manualmente para um goal que não é nenhum dos 4 reconhecidos (`add-source`, `add-test-source`, `add-resource`, `add-test-resource`), a execução é silenciosamente ignorada (não é um erro de inferência — o produto nunca falha ao ler um pom válido só porque um plugin de terceiros tem configuração que ele não entende).
- Múltiplas `<source>`/`<resource>` dentro da mesma `<execution>` (o `register_directory_role` desta ferramenta nunca escreve mais de uma, mas um pom editado manualmente pode) são todas lidas — nenhuma é descartada.
