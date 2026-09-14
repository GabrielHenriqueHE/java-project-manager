# Design de Interface — TUI "mvnforge"

> Fonte: instrução de implementação fornecida pelo usuário em 2026-09-13,
> extraída de duas capturas de tela do protótipo de referência
> (project-buddy-cli.lovable.app). Reproduzida aqui na íntegra como
> referência de design canônica para a reformulação da TUI (ver
> `specs/phases/phase-3-redesign-tui/`). O usuário rejeitou o layout da
> Fase 1/2 (fluxo Dashboard → Import → ProjectDetail em telas separadas)
> em favor deste layout de painel único com 3 colunas.

## Estrutura geral da tela

Três colunas de largura fixa/proporcional + cabeçalho de uma linha no topo
+ rodapé de uma linha na base. **Não** é um grid 2x2.

- **Coluna 1** (esquerda, ~16% da largura): Painel [1] PROJETOS (alto) sobre Painel [3] MÓDULOS.
- **Coluna 2** (meio, ~40% da largura): Painel [2] METADADOS (topo) sobre Painel [4] BOM + DEPENDÊNCIAS.
- **Coluna 3** (direita, ~44% da largura): Painel [5] ESTRUTURA, único, ocupa a coluna inteira.

Proporções aproximadas, medidas visualmente — não são valores exatos.

## Cabeçalho (1 linha, topo, largura total)

- Esquerda: "mvnforge" em destaque (bold/cor de marca), seguido da coordenada Maven completa do projeto selecionado. Exemplo: `br.com.orion:orion-platform:1.4.0-SNAPSHOT`.
- Direita (alinhado à borda direita): `java <versao> · maven · <N> mod · <N> dep`.

Implementação sugerida: cabeçalho customizado (não o `Header` padrão do Textual), Static fixa no topo com layout Horizontal (bloco esquerdo + spacer + bloco direito).

## Coluna 1 — Projetos + Módulos

### Painel [1] PROJETOS
- Header do painel: `[1] PROJETOS` à esquerda, `<N> repos` à direita.
- Lista de projetos, um por linha: `<marcador> <nome>  <versao>`.
  - `●` (preenchido) + fundo teal sólido no item selecionado.
  - `○` (vazio) nos demais, sem fundo.
- Estado vazio: "carregando…" em cor secundária/dimmed.
- Ocupa a maior parte da altura da coluna.
- Widget sugerido: `ListView`/`OptionList` dentro de um painel customizado com header próprio.

### Painel [3] MÓDULOS
- Header: `[3] MÓDULOS` à esquerda, nome do projeto ativo à direita.
- Lista em árvore com conectores `├─`/`└─`: `<nome-modulo>  <packaging>` (packaging em cor secundária).
- Item selecionado com fundo destacado (mesmo estilo do painel [1]).
- Widget sugerido: `Tree` com guides customizados, ou lista simples com conectores desenhados manualmente se o estilo padrão do `Tree` não bater visualmente.

## Coluna 2 — Metadados + BOM

### Painel [2] METADADOS
- Header: `[2] METADADOS` à esquerda, `enter edita` à direita.
- Tabela chave-valor: chave em cor secundária à esquerda; valor em destaque (branco/bold) em coluna fixa à direita.
- Campos, nesta ordem: `name`, `groupId`, `artifactId`, `version`, `java.version`, `packaging`, `description`.
- `description` pode ocupar múltiplas linhas, mantendo alinhamento da coluna de valor.
- Estado vazio: "nenhum projeto selecionado" em cor secundária.
- Widget sugerido: `DataTable` sem grade visível, ou `Static` com layout Grid via CSS, duas colunas.

### Painel [4] BOM + DEPENDÊNCIAS
- Header: `[4] BOM + DEPENDENCIAS` à esquerda, nome do módulo BOM ativo à direita (ex.: `orion-bom`).
- Cada entrada: `bom <groupId>:<artifactId em destaque> <versao> · <scope>`. Exemplo: `bom org.springframework.boot:spring-boot-dependencies 3.3.4 · import`.
- Estado vazio: "nada declarado. pressione n" em cor secundária.
- Painel maior; resto do espaço fica vazio quando há poucas entradas.

## Coluna 3 — Estrutura

### Painel [5] ESTRUTURA
- Header: `[5] ESTRUTURA` à esquerda, `space alterna · <modulo ativo>` à direita.
- **Bloco 1** (topo): checklist de diretórios-padrão com `[x]` (marcado, cor de destaque) ou `[ ]` (desmarcado, cor secundária):
  ```
  src/main/java
  src/main/resources
  src/test/java
  src/test/resources
  src/main/webapp
  src/main/proto
  src/it/java
  docs
  ```
- **Bloco 2** (abaixo do checklist, sem separador de painel visível): árvore de diretórios do projeto inteiro, estilo `tree` (`├──`, `│`, `└──`), mostrando cada módulo com `pom.xml` (raiz anotada com "(packaging: pom)"), `src/main/java/` com o pacote Java completo abaixo (ex.: `└── br/com/orion/orionbom/`), `src/main/resources/`, `src/test/java/`.
- Estado vazio: "sem modulos. pressione n" (só se não houver módulos).
- Widget sugerido: `Tree` nativo, ou `RichLog`/`Static` com string pré-formatada para controle total do alinhamento.

## Rodapé — dois modos

### Modo normal (padrão)
- Esquerda: badge com fundo teal sólido "PAINEL \<n\>" + status em texto simples (ex.: "pronto").
- Direita: atalhos separados por espaço duplo, formato `<tecla(s)> <ação>`, ex.: `1-5/tab painel   j/k mover   enter abrir/editar   n novo   e edita`.
- Atalhos exibidos devem ser **contextuais** ao painel/widget focado — ex.: "d remover" só aparece em painéis onde remover um item faz sentido (Projetos, Módulos, BOM+Dependências), não em Metadados ou Estrutura (que usa "space alterna" no lugar).
- Usar o `Footer` nativo do Textual (renderiza automaticamente os `BINDINGS` do widget focado) — declarar `BINDINGS` por painel/widget, não globalmente na `App`.

### Modo comando (ativado ao digitar ":")
- Substitui a barra inteira por uma linha: `:<comando> em <contexto> (<hint de formato>) > digite e pressione enter · esc cancela`. Exemplo: `:dependencia em orion-bom (groupId:artifactId:version) > digite e pressione enter · esc cancela`.
- Implementação sugerida: `Input` que substitui o `Footer` temporariamente, ativado por binding global de ":", placeholder dinâmico conforme contexto.

## Paleta e estilo visual (aproximado)

- Fundo: quase preto / azul muito escuro.
- Headers de painel e nome do app: ciano/teal.
- Valores em destaque: branco ou dourado, conforme o campo.
- Texto secundário (labels, placeholders de estado vazio, conectores de árvore): cinza apagado.
- Item selecionado em listas: fundo teal sólido, texto contrastante.
- Bordas de painel: linha simples de caixa, cantos retos, sem sombra/gradiente.

## Fora do escopo

O selo "Edit with Lovable" das capturas é overlay da plataforma de hospedagem do protótipo — não faz parte do design da TUI, ignorar.

## Observação do usuário (não confirmada pelas capturas)

O bind "d remover" foi listado como candidato contextual em Projetos/Módulos/BOM por lógica de UX, mas nenhuma captura mostrou esses painéis focados com atalhos diferentes — é inferência, não algo visto diretamente na imagem.

## Decisões de implementação tomadas (lacunas preenchidas durante a Fase 3)

Estas decisões preencheram pontos que a especificação acima não define explicitamente. Ver `specs/phases/phase-3-redesign-tui/design.md` para o raciocínio completo de cada uma.

1. Painel [2] Metadados reflete o módulo atualmente selecionado no Painel [3] Módulos (não só o projeto raiz) — mesma semântica que a antiga `ProjectDetailScreen`.
2. Painel [5] Estrutura mantém um cursor de "módulo ativo" **independente** da seleção do Painel [3], alternado via `space` — é o que explica o texto `<modulo ativo>` no header do painel coexistir com a seleção do Painel [3].
3. `enter edita` (Metadados) e `n novo`/`d remover` em BOM+Dependências apontam para mutações (`update_metadata`, `update_dependency`) ainda não implementadas no `MavenAdapter` (stubs desde a Fase 1). A UI expõe os binds/hints conforme o design visual, mas a ação mostra uma notificação "ainda não implementado" em vez de silenciosamente não fazer nada ou quebrar.
4. "d remover" implementado apenas onde a mutação já existe: Painel [1] (remove do registry) e Painel [3] (`remove_module`, com o mesmo fluxo de `DependentModuleConflict` → `ConfirmModal` já construído na Fase 2). Não implementado em Painel [4] pelo motivo do item 3.
5. Modo comando (":") implementado como mecanismo genérico e funcional para o caso `modulo <nome>` (atalho para `add_module` sem abrir o formulário completo); outros comandos (`dependencia ...`) mostram a mesma notificação "ainda não implementado" do item 3, já que a mutação subjacente não existe.
