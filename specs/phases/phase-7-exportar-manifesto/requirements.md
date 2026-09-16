# Fase 7 — Exportar Projeto para Manifesto — Requirements

Operação inversa da Fase 6 (`phases/phase-6-criar-projeto/`): lá, um manifesto YAML materializa um projeto Maven novo (`BuildToolAdapter.create_project`). Aqui, um projeto **já existente** (já registrado/inferido pela ferramenta) é serializado para um arquivo de manifesto YAML no mesmo formato — útil para versionar a "forma" de um projeto, recriá-lo depois, ou usar um projeto existente como ponto de partida para um novo via `create_project`.

Diferença importante em relação à Fase 6: `create_project` precisa do `MavenAdapter` porque escreve arquivos de build reais (`pom.xml`, `build-helper-maven-plugin`). Exportar não escreve nenhum arquivo de build — parte de um `Project`/`Module` **já inferido**, que já é uniforme entre build tools (essa é a razão de existir do modelo de domínio: decisão #3 do decision log, `00-overview.md`), e só serializa esse objeto já em memória para YAML. Por isso esta fatia **não** adiciona nenhum método ao `BuildToolAdapter` — a conversão `Module → ModuleManifest` é uma função pura em `src/manager/manifest.py`, o mesmo módulo que já hospeda `ModuleManifest`/`load_manifest`/`validate_manifest_tree` desde a Fase 6.

## Escopo

**Dentro:**
- `to_manifest(module: Module) -> ModuleManifest` (`src/manager/manifest.py`): converte um `Module` já inferido para o formato de manifesto, descartando os campos que só existem em disco (`relative_path`, `build_file`) e o `tree` de `DirectoryStructure` (só serve para exibição da árvore no Painel [5]; `create_project` nunca lê `tree` na materialização — ver `phase-6-criar-projeto/design.md`). Recursivo para toda a árvore de submódulos.
- `dump_manifest(manifest: ModuleManifest, path: Path) -> None`: serializa para YAML em `path`, **sobrescrevendo** se já existir (diferente da regra de `create_project` para `destination_path`, que recusa um diretório não-vazio — aqui o destino é um único arquivo, não uma árvore de código real, e reexportar para o mesmo caminho é a operação mais comum esperada).
- TUI: novo fluxo no Painel [1] PROJETOS (binding `e`) que exporta o projeto atualmente aberto para um caminho de arquivo informado pelo usuário.

**Fora (fatias futuras ou fora do produto):**
- Exportar um submódulo isolado (em vez da árvore inteira a partir da raiz) — esta fatia exporta sempre o projeto inteiro, mesma granularidade de `create_project`.
- Qualquer forma de "diff" entre um manifesto exportado antigo e o estado atual do projeto.
- Round-trip automático/validação cruzada na própria TUI (ex.: exportar e já reimportar num clique) — o usuário decide separadamente se quer usar o manifesto exportado com `create_project` depois.

## User stories

- Como desenvolvedor Java, quero exportar a estrutura de um projeto que já gerencio para um arquivo YAML, para versionar essa estrutura ou usá-la como ponto de partida para criar um projeto novo semelhante.

## Critérios de aceite

- Exportar um projeto multi-módulo com BOM produz um YAML que, lido de volta com `load_manifest` e passado para `create_project` num diretório novo, materializa um projeto estruturalmente equivalente ao original (mesmos módulos, dependências diretas/gerenciadas, diretórios convencionais e customizados).
- O YAML exportado não contém `relative_path`, `build_file`, nem a árvore (`tree`) de `DirectoryStructure` — só os campos que `ModuleManifest` já aceita como entrada.
- Exportar para um caminho cujo arquivo já existe sobrescreve sem pedir confirmação.
- Tentar exportar sem nenhum projeto aberto não abre o formulário — notifica erro direto (mesmo padrão de `add_dependency`/`register_build_source` quando `self.project is None`).

## Requisitos não funcionais

- Nenhuma escrita em arquivo de build (`pom.xml` ou equivalente) — a exportação é estritamente leitura do modelo em memória + escrita de um único arquivo YAML.
- `to_manifest`/`dump_manifest` não pertencem a nenhum adapter concreto — funcionam sobre `Module`, que já é o mesmo tipo produzido por `infer_structure` de qualquer `BuildToolAdapter` (Maven hoje; Gradle no futuro), sem precisar saber qual foi.

## Dependências de outras features

- Depende de `phase-6-criar-projeto` (mesmo tipo `ModuleManifest`, mesmo dialeto YAML — reexportar e reimportar precisam ser simétricos).
- Depende de [[05-inferencia-de-projeto-existente]] (a fonte dos dados exportados é sempre um `Project` já inferido).

## Riscos / limitações conhecidas

- Igual à Fase 6: o manifesto (agora também como formato de *saída*) precisa continuar em sincronia com o modelo de domínio real — `to_manifest` reaproveita os mesmos tipos Pydantic (`metadata`, `dependencies`, `directory_structure` são atribuídos diretamente, sem remapeamento manual campo a campo), o que minimiza esse risco por construção.
- `exclude_defaults=True` na serialização (ver design) mantém o YAML enxuto, mas significa que um campo que coincide com o valor default do modelo (ex.: `packaging: jar`) não aparece explicitamente no arquivo — comportamento aceito porque `load_manifest` aplica o mesmo default na leitura de volta, então o round-trip continua correto.
