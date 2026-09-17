# Fase 24 — Iniciar Projeto do Zero — Requirements

Fecha uma lacuna deixada em aberto desde o início do produto: `specs/features/01-gerenciamento-de-projetos/requirements.md` (linha 20, antes desta fase) listava "criar um projeto Java do zero (scaffold completo)" em **"Fora"**, e `specs/phases/phase-6-criar-projeto/requirements.md` (linha 20) explicitamente adiava "editar o manifesto pela própria TUI (formulário visual para montar a árvore)" — a Fase 6 só lê e consome um manifesto YAML já escrito à mão pelo usuário em outro editor. Esta fase adiciona o formulário que faltava, mas com escopo deliberadamente menor do que "montar a árvore inteira visualmente": um único módulo raiz, sem submódulos/BOM/dependências no formulário.

## Escopo desta fatia

**Dentro:**
- Novo `InitProjectScreen` (`src/manager/screens/init_project.py`) com campos build tool / groupId / artifactId / version / destino, sem nenhum manifesto YAML envolvido — o `ModuleManifest` é montado inteiramente em memória a partir dos campos do formulário.
- Reaproveita `BuildToolAdapter.create_project`, já implementado de ponta a ponta para Maven (Fase 6) e Gradle (Fase 23) — nenhuma mudança em adapter/domínio/`ModuleManifest`.
- Um único módulo raiz, `packaging="jar"` fixo (sem submódulos, sem dependências, sem BOM no formulário).
- Novo binding `i` ("iniciar") no Painel [1] PROJETOS; `MainScreen.init_project()` reaproveitando o mesmo callback compartilhado `_on_project_registered` já usado por `import_project`/`clone_project`.

**Fora (fatias futuras ou fora do produto):**
- Submódulos, BOM ou dependências diretas no formulário — para isso o fluxo de manifesto (Fase 6, binding `c`) continua sendo o caminho.
- Campo de packaging no formulário (fixo em `jar`; um módulo `pom` solitário sem submódulos/BOM é um caso válido-mas-incomum que o domínio já tolera, só não é oferecido por este formulário).
- Corrigir o hardcode de `MavenAdapter` em `CreateProjectScreen` (fluxo de manifesto da Fase 6) — gap pré-existente desde a Fase 6/23 (o fluxo de manifesto não permite escolher Gradle, mesmo `GradleAdapter.create_project` já existindo desde a Fase 23), deliberadamente não corrigido aqui para manter esta fase restrita ao novo formulário; candidato a uma fatia futura independente.
- Templates/catálogo de manifestos pré-prontos (exclusão já herdada da Fase 6).

## User stories

- Como desenvolvedor Java, quero preencher um formulário simples (build tool, coordenadas Maven/Gradle, destino) e ter um projeto novo de um único módulo materializado em disco, sem precisar escrever um manifesto YAML à mão primeiro.

## Critérios de aceite

- Dado build tool=maven, artifactId, groupId e version preenchidos e um destino vazio/inexistente, quando confirmo, então um `pom.xml` válido é criado no destino e o projeto aparece registrado e selecionado.
- Dado build tool=gradle, artifactId preenchido (groupId/version podem ficar vazios, já que Gradle não exige) e um destino vazio/inexistente, quando confirmo, então `settings.gradle`+`build.gradle` são criados no destino e o projeto aparece registrado e selecionado.
- Dado artifactId, destino ou build tool ausentes/inválidos, quando confirmo, então uma mensagem de erro aparece no formulário e nada é escrito em disco.
- Dado build tool=maven sem groupId ou sem version, quando confirmo, então o erro já existente do adapter ("Modulo raiz nao tem parent para herdar: groupId e version sao obrigatorios") aparece no formulário e nada é escrito em disco.
- Dado um destino que já existe e não está vazio, quando confirmo, então o erro já existente do adapter ("... ja existe e nao esta vazio") aparece no formulário e nada é escrito em disco.
- Dado o formulário aberto, quando cancelo (`escape`), então nada é criado e volto para a tela principal.

## Requisitos não funcionais

- Nenhuma regra de negócio (obrigatoriedade de groupId/version por build tool, validação de destino) é duplicada na camada de TUI — toda validação de negócio vem dos `ValueError` que `MavenAdapter`/`GradleAdapter.create_project` já levantam, exibidos direto no formulário.
- Mesma garantia de todas as fatias de `create_project` anteriores: o projeto retornado é sempre `infer_structure(destination_path)`, nunca um objeto montado à mão.

## Dependências de outras features

- Depende de `create_project` já implementado para ambas as build tools (Fases 6 e 23) — nenhuma feature nova é necessária.

## Riscos / limitações conhecidas

- O formulário deliberadamente não oferece submódulos/BOM/dependências; quem precisa disso continua usando o fluxo de manifesto (`c`).
- O campo de build tool é texto livre validado contra um conjunto fixo (`{"maven", "gradle"}`), não um `Select` — decisão de consistência com o resto da base de código, que não usa `Select` em nenhum outro formulário (ver `screens/widgets/build_source_form.py`'s `_VALID_ROLES` como precedente do mesmo padrão).
