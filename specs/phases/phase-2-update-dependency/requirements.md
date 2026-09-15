# Fase 2 — Atualizar Dependência — Requirements

Quarta e última fatia de mutação de [[03-gerenciamento-de-modulos]] planejada até aqui: implementar `update_dependency` de ponta a ponta (Maven), tanto no adapter quanto na TUI (Painel [4] BOM + DEPENDÊNCIAS, binding `n` já existente e hoje mostrando aviso "nao implementado"). Depende de `update_metadata` (`phase-2-update-metadata`) apenas na ordem de implementação, não na API.

## Escopo

**Dentro:**
- `MavenAdapter.update_dependency(project, module_name, dependency: Dependency) -> Project` funcional: adiciona uma nova `<dependency>` ou atualiza uma existente (match por `(groupId, artifactId)`) em `<dependencies>` (se `dependency.managed=False`) ou em `<dependencyManagement><dependencies>` (se `dependency.managed=True`) do módulo indicado. Escreve `groupId`, `artifactId`, `version`, `scope`, `type`, `classifier` (os campos presentes no modelo `Dependency`).
- Cria as seções `<dependencies>`/`<dependencyManagement><dependencies>` se ainda não existirem no pom, respeitando a ordem de elementos do XSD do POM (mesma infraestrutura de `phase-2-update-metadata`).
- Wiring na TUI: Painel [4] (`BomPanel`) — binding `n` abre `DependencyFormScreen`; a dependência é sempre `managed=True` (o painel é especificamente de BOM/dependências gerenciadas) e o módulo alvo é o módulo atualmente selecionado no Painel [3] (Módulos), ou a raiz se nenhum estiver selecionado.
- Validação: o módulo alvo precisa ter `packaging=pom` para receber uma entrada gerenciada (mesma restrição que `add_module` já aplica a módulos-pai) — evita que uma entrada de `dependencyManagement` seja gravada num módulo `jar` comum, o que o Maven aceita mas não é o padrão esperado por este produto (a UI/documentação assume que gerenciamento de versão vive num módulo agregador ou dedicado a BOM).
- Entrada gerenciada (`managed=True`) exige `version` (obrigatório); entrada direta (`managed=False`) não exige (pode herdar do `dependencyManagement`).

**Fora (fora do escopo desta fatia ou do produto por ora):**
- Remover uma dependência já declarada pela TUI — a interface `BuildToolAdapter` não define um `remove_dependency`/`remove_managed_dependency` como operação de primeira classe (o `MavenPomWriter.remove_dependency`/`remove_managed_dependency` existentes só são usados internamente por `remove_module`); adicionar essa operação é trabalho futuro, não desta fatia.
- Adicionar/editar uma dependência **direta** (`managed=False`) de um módulo qualquer pela TUI — não há painel para "dependências diretas de um módulo" no layout atual (`specs/design/tui-layout.md`); o Painel [4] é especificamente BOM. O adapter suporta `managed=False` (usado pelos testes e por `add_module` na criação inicial), mas não há gancho de UI nesta fatia.
- Editar uma entrada existente clicando nela na lista — `n` sempre abre um formulário em branco; para "editar", o usuário digita novamente as mesmas coordenadas com o novo valor (comportamento de upsert, não um fluxo de edição in-line).
- Resolver/validar se a dependência informada realmente existe num repositório Maven — o adapter só grava o que foi digitado, sem nenhuma chamada de rede.

## User stories

- Como desenvolvedor Java, quero declarar uma dependência gerenciada (BOM) num módulo agregador sem editar `<dependencyManagement>` manualmente.
- Como desenvolvedor Java, quero que declarar novamente uma dependência já existente (mesmo `groupId:artifactId`) atualize a versão/escopo em vez de duplicar a entrada.

## Critérios de aceite

- Adicionar uma dependência gerenciada nova a um módulo `packaging=pom` sem `<dependencyManagement>` cria a seção inteira na posição correta do pom.
- Repetir a mesma `groupId:artifactId` com uma versão diferente atualiza a entrada existente em vez de criar uma duplicata.
- Tentar adicionar uma entrada gerenciada sem `version` falha com erro claro; nenhuma escrita ocorre.
- Tentar adicionar uma entrada gerenciada a um módulo com `packaging` diferente de `pom` falha com erro claro; nenhuma escrita ocorre.
- Na TUI, cancelar o formulário não altera nada; confirmar adiciona/atualiza a entrada e o Painel [4] reflete o novo estado (via re-inferência, refletindo em `project.managed_dependencies`).

## Requisitos não funcionais

- Mesma garantia das fatias anteriores: o retorno é sempre uma re-inferência via `infer_structure` (ver [[05-inferencia-de-projeto-existente]]).
- Reaproveita `xml_utils.ensure_child_in_order` (de `phase-2-update-metadata`) para inserir `<dependencyManagement>`/`<dependencies>` respeitando a ordem do XSD, em vez de duplicar essa lógica.

## Dependências de outras features

- Depende de [[05-inferencia-de-projeto-existente]].
- Depende de `phase-2-update-metadata` na ordem de implementação (reaproveita `ensure_child_in_order`), mas não há acoplamento de API entre as duas.

## Riscos / limitações conhecidas

- Um projeto sem nenhum módulo com `packaging=pom` e `dependencyManagement` ainda não tem um "módulo BOM" reconhecido por `is_bom` (que exige `managed_dependencies` não-vazio); a primeira dependência gerenciada precisa ser adicionada a um módulo agregador (`packaging=pom`) escolhido pelo usuário via seleção no Painel [3] — depois disso `is_bom` passa a reconhecê-lo automaticamente na próxima inferência.
- Mesma limitação de formatação do lxml/libxml2 já registrada nas fatias anteriores (tag `<project>` pode ser reformatada).
