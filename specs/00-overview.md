# Visão geral — Java Project Manager (jpm)

## Problema

Projetos Java seguem sempre a mesma estrutura de diretórios, pacotes e módulos, mas a manutenção dessa estrutura é manual e repetitiva. O caso mais doloroso é o gerenciamento de módulos Maven: adicionar um módulo exige editar `<modules>` no pom pai, registrar dependências no BOM (`dependencyManagement`), e ajustar os módulos que passam a depender dele; remover um módulo exige o inverso — e nada disso é validado automaticamente, então é fácil deixar o projeto num estado inconsistente (pom referenciando módulo inexistente, dependência quebrada, BOM desatualizado).

## Objetivo do produto

Uma aplicação **TUI reutilizável** que:
1. Facilita o gerenciamento de projetos (criação, remoção, listagem).
2. Facilita a manipulação de metadados vinculados a projetos.
3. Facilita adição, remoção e atualização de módulos dentro de um projeto, mantendo consistência entre pom pai, BOM e módulos dependentes.
4. Facilita a definição da estrutura de diretórios do projeto/módulos.
5. Infere a estrutura de um projeto Java já existente a partir dos seus arquivos de build reais.

Restrição arquitetural: a ferramenta deve funcionar **independente da build tool** usada pelo projeto Java gerenciado.

## Glossário

| Termo | Significado |
|---|---|
| **Projeto (Project)** | Um projeto Java gerenciado pela ferramenta; possui um `root_module` e uma build tool associada. |
| **Módulo (Module)** | Unidade de código dentro de um projeto; pode conter submódulos (árvore). Em Maven, corresponde a um `pom.xml`. |
| **BOM** | Módulo (ou seção) responsável por centralizar versões de dependências via `dependencyManagement`. Em Maven, tipicamente um módulo `packaging=pom`. |
| **Adapter** | Componente que traduz entre o modelo de domínio agnóstico e os arquivos reais de uma build tool específica (ex.: `MavenAdapter`). |
| **Inferência (infer_structure)** | Processo de ler os arquivos de build reais de um projeto existente e montar o modelo de domínio correspondente, sem exigir nenhum manifesto próprio. |
| **Registry** | Lista leve, mantida pela aplicação (fora do modelo de domínio), de quais projetos o usuário já registrou/abriu. |

## Decisões arquiteturais (decision log)

Estas decisões foram confirmadas com o usuário e **não devem ser reabertas** sem justificativa nova:

1. **Metodologia: Spec-Driven Development leve e customizada.** Sem ferramenta externa (ex.: spec-kit). Os specs vivem neste diretório (`specs/`) e seguem o formato descrito abaixo. Motivo: controle total sobre o formato, sem overhead de integrar uma ferramenta de terceiros para um fluxo que pode ser mantido manualmente.
2. **Stack da TUI: Python + [Textual](https://textual.textualize.io/).** O repositório já era Python (uv, pydantic) e já tinha uma estrutura de pastas `screens/`/`screens/widgets/` sugerindo Textual.
3. **Modelo de domínio próprio + Adapters por build tool.** Em vez de manipular `pom.xml` (ou equivalente) diretamente e ad-hoc, existe um modelo Pydantic agnóstico (`Project`, `Module`, `Dependency`, etc.) e uma interface `BuildToolAdapter` implementada por build tool (Maven agora; Gradle e outras no futuro). Isso é o que viabiliza o requisito de "funcionar independente da build tool".
4. **Sem manifesto próprio de projeto.** O estado estrutural de um projeto (módulos, dependências, diretórios) nunca é persistido pela ferramenta — é sempre derivado ao vivo dos arquivos de build reais via `infer_structure()`. Isso evita drift entre o que a ferramenta "acha" que existe e o que realmente está no disco (ex.: após um `git pull` ou edição manual). O único estado persistente da aplicação é o **registry** de projetos conhecidos (path + build tool), guardado fora do projeto Java gerenciado, em `~/.config/java-project-manager/registry.json`.
5. **lxml para parsing/escrita de XML (Maven).** Necessário para lidar corretamente com o namespace do POM, preservar formatação/comentários do arquivo original (minimizar diffs em arquivos versionados do usuário) e ter XPath completo.

## Estrutura de specs

```
specs/
  00-overview.md              # este arquivo
  design/                     # referências de design duráveis, cross-feature (ex.: layout da TUI)
  features/<n>-<nome>/        # o "o quê" de cada capacidade — estável entre fases
    requirements.md           # user stories + critérios de aceite
    design.md                 # solução técnica da feature
    tasks.md                  # aponta para a(s) fase(s) que implementam a feature
  phases/<fase>/               # o "quanto agora" — fatia de execução real
    requirements.md           # subconjunto de aceite reduzido para esta fase
    design.md                 # decisões concretas de arquitetura desta fase
    tasks.md                  # checklist executável e verificável desta fase
```

`features/*` não duplica o checklist de execução — cada `tasks.md` de feature referencia de volta a fase que a implementa (parcial ou totalmente). A fonte de verdade sobre "o que já foi feito" é sempre `phases/<fase>/tasks.md`.

## Fases

- **Fase 1 — Fundação** (`phases/phase-1-fundacao/`, concluída): estrutura de specs, modelo de domínio, interface de adapter + `MavenAdapter.infer_structure`, scaffold Textual navegável em modo leitura.
- **Fase 2 — Mutações** (em andamento): fatias concluídas em `phases/phase-2-remover-modulo/` (`remove_module`, com detecção de dependentes) e `phases/phase-2-add-module/` (`add_module`, com criação de diretório/pom e herança de groupId/version). Fatias seguintes: `update_dependency`, `update_metadata`.
- **Fase 3 — Reformulação da TUI** (`phases/phase-3-redesign-tui/`): o layout de telas separadas (Dashboard → Import → ProjectDetail) da Fase 1-2 foi substituído por um layout de painel único com 3 colunas e 5 painéis simultâneos ("mvnforge"), especificado em `design/tui-layout.md`. Nenhuma mudança na camada de domínio/adapters/services — apenas na apresentação.
- Fases futuras: edição de estrutura de diretórios customizada pela TUI, suporte a Gradle.
