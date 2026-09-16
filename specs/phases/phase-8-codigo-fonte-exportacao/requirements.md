# Fase 8 — Código-Fonte na Exportação — Requirements

Terceira fatia consecutiva do ciclo criar/exportar (depois da Fase 6, `create_project`, e da Fase 7, `to_manifest`/`dump_manifest`): até aqui exportar um projeto produz só a **estrutura** (módulos, dependências, diretórios) — recriar a partir desse manifesto sempre gera diretórios vazios, nunca o conteúdo real dos arquivos. Esta fatia permite preservar também o **código-fonte** de módulos escolhidos na exportação, para que criar um projeto novo a partir do manifesto já venha com uma base de código consolidada — não só o esqueleto de pastas. Caso motivador: módulos `shared-*` (bibliotecas/utilitários tipicamente reaproveitados entre projetos).

## Escopo

**Dentro:**
- `export_source_files(project, manifest_path, pattern) -> list[str]` (`src/manager/manifest.py`): copia os diretórios já rastreados em `directory_structure` (`source_dirs`, `test_dirs`, `resource_dirs`, `test_resource_dirs`) de cada módulo cujo `artifactId` bate com `pattern` (glob, via `fnmatch`) para uma **pasta irmã** do arquivo de manifesto: `<manifest sem extensão>.files/<artifactId>/<caminho-relativo>`. Retorna os `artifactId` que bateram (lista vazia se nenhum).
- `MavenAdapter.create_project` ganha um parâmetro opcional `source_root: Path | None`: quando informado, para cada diretório que a materialização for criar, se existir `source_root/<artifactId>/<caminho-relativo>`, **copia** esse conteúdo em vez de só criar o diretório vazio.
- TUI: `ExportManifestScreen` ganha um campo opcional de padrão de módulos (glob, ex. `shared-*`); `CreateProjectScreen` detecta automaticamente (por convenção de nome/local) uma pasta `.files` ao lado do manifesto escolhido e a usa como `source_root`, sem campo novo nesse formulário.

**Fora (fatias futuras ou fora do produto):**
- Embutir conteúdo de arquivo no próprio YAML (base64/texto inline) — decisão explícita: pasta irmã, não YAML monolítico (ver design).
- Selecionar módulos por qualquer critério além de padrão de nome (glob) — ex. checklist interativo na TUI, seleção por caminho, etc.
- Qualquer filtragem de conteúdo (ex.: por extensão de arquivo, `.gitignore`) — copia tudo que estiver dentro dos diretórios já rastreados pela ferramenta (nunca inclui `target/`, `.git/`, etc., porque esses nunca entram em `directory_structure`).
- Atualizar/sincronizar incrementalmente uma pasta `.files` já existente com mudanças no projeto original — cada exportação com padrão sobrescreve/mescla via `copytree(dirs_exist_ok=True)`, sem noção de diff.

## User stories

- Como desenvolvedor Java, quero exportar meus módulos `shared-*` com o código-fonte real incluído, para poder iniciar um projeto novo já com essas bibliotecas prontas, sem recriar as classes manualmente.

## Critérios de aceite

- Exportar com um padrão que bate com um ou mais módulos cria `<manifest>.files/<artifactId>/...` com cópias reais (byte-idênticas) dos arquivos desses módulos; módulos que não batem não geram pasta nenhuma.
- Exportar sem padrão (campo vazio) não cria nenhuma pasta `.files` — comportamento idêntico ao da Fase 7, sem regressão.
- Criar um projeto a partir de um manifesto que tem uma pasta `.files` ao lado materializa os arquivos reais nos módulos correspondentes (conteúdo idêntico ao exportado); módulos sem correspondência em `.files` continuam recebendo diretórios vazios, como hoje.
- Criar um projeto a partir de um manifesto **sem** pasta `.files` ao lado (ou chamando `create_project` sem `source_root`) tem exatamente o mesmo comportamento de antes desta fatia — nenhuma regressão nos testes/fluxos existentes.

## Requisitos não funcionais

- `to_manifest`/`dump_manifest` (Fase 7) permanecem intocados — a nova função é aditiva, chamada separadamente pela TUI depois de `dump_manifest`.
- `create_project`/`_materialize` continuam retornando sempre `infer_structure(destination_path)` — os arquivos copiados passam pelo mesmo caminho de verdade (o que está em disco depois de materializar) que qualquer outra mutação do adapter.
- Nenhuma dependência nova (usa só `shutil`/`fnmatch`, biblioteca padrão).

## Dependências de outras features

- Depende de `phase-6-criar-projeto` (`create_project`/`_materialize`) e `phase-7-exportar-manifesto` (`to_manifest`/`dump_manifest`, `ExportManifestScreen`/`CreateProjectScreen`).

## Riscos / limitações conhecidas

- A pasta `.files` "viaja" com o manifesto só por convenção de nome/local (mesmo diretório, mesmo nome-base) — se o usuário mover só o `.yaml` sem a pasta (ou vice-versa), a criação simplesmente não encontra `source_root` e cai no comportamento padrão (diretório vazio), sem erro — comportamento degradado silenciosamente aceitável (não é dado crítico perdido, é a estrutura que já está no YAML).
- Reexportar com o mesmo padrão para o mesmo destino faz merge por cima de uma pasta `.files` já existente (`copytree(dirs_exist_ok=True)`) — arquivos removidos do projeto original desde a última exportação **não** são removidos da pasta `.files` (união, não espelho exato). Aceito nesta fatia; um comportamento de "espelho exato" fica para trabalho futuro se necessário.
