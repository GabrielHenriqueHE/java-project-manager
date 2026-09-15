# Fase 5 — Remover Dependência — Requirements

Primeira metade do item 2 do roadmap (`specs/00-overview.md`) sobre [[03-gerenciamento-de-modulos]]: `phase-2-update-dependency` deixou registrado como "fora" que a interface `BuildToolAdapter` não tinha `remove_dependency` como operação de primeira classe (o `MavenPomWriter.remove_dependency`/`remove_managed_dependency` já existiam, mas só eram usados internamente por `remove_module`). Esta fase fecha essa lacuna para o caso de uso do Painel [4]: remover uma entrada **gerenciada** (BOM) já declarada.

A segunda metade do item 2 ("adicionar/editar dependência **direta** de um módulo qualquer pela TUI") fica deferida — não há painel para "dependências diretas de um módulo" no layout atual (`specs/design/tui-layout.md`), então essa fatia exigiria decisão de design de UI nova, fora do escopo desta fase.

## Escopo

**Dentro:**
- `BuildToolAdapter.remove_dependency(project, group_id, artifact_id)` novo método na interface: remove uma dependência **gerenciada** (`managed=True`) identificada por `(groupId, artifactId)`, devolve o projeto re-inferido.
- Sem `module_name` no parâmetro: diferente de `update_dependency` (onde é preciso escolher em qual módulo criar a entrada), aqui a entrada já existe em exatamente um módulo — o adapter varre a árvore de módulos procurando quem tem essa dependência gerenciada e remove de lá. Isso casa com o Painel [4], que já mostra `project.managed_dependencies` como uma lista achatada (sem expor de qual módulo cada entrada veio).
- `MavenAdapter.remove_dependency`: percorre a árvore (`Module.dependencies`, que já inclui as gerenciadas do próprio módulo com `managed=True`), acha o módulo dono, chama o `MavenPomWriter.remove_managed_dependency` já existente.
- Wiring na TUI: Painel [4] (`BomPanel`) ganha o binding `d` (mesma convenção de "remover" dos Painéis 1/3/5) sobre a entrada atualmente destacada na lista.
- Sem modal de confirmação: mesmo padrão já usado por `remove_module` quando não há conflito (remove direto) — aqui não há checagem de "dependentes" desta fatia (ver Riscos).

**Fora (fatias futuras ou fora do produto):**
- Adicionar/editar dependência **direta** (`managed=False`) de um módulo qualquer pela TUI — sem painel para isso no layout atual; fica deferido.
- Detectar/avisar se outros módulos têm uma dependência **direta** cuja versão dependia dessa entrada gerenciada (ao contrário de `remove_module`, que bloqueia com `DependentModuleConflict` se houver dependentes) — remover uma entrada de `dependencyManagement` não deixa o pom em estado inconsistente do ponto de vista de XML (só faz o Maven exigir uma versão explícita na próxima build); adicionar essa checagem é trabalho futuro, não desta fatia.
- Editar uma entrada existente (ex.: só mudar a versão) — isso já é coberto por `update_dependency` (upsert); esta fase é só remoção.

## User stories

- Como desenvolvedor Java, quero remover uma dependência gerenciada que declarei por engano ou que não é mais necessária, sem sair da TUI para editar o `pom.xml` manualmente.

## Critérios de aceite

- Destacar uma entrada na lista do Painel [4] e pressionar `d` remove a entrada gerenciada correspondente do `pom.xml` do módulo dono; a lista atualiza e mostra uma a menos.
- Remover a última entrada gerenciada de um módulo volta o Painel [4] ao estado vazio ("nada declarado. pressione n").
- Tentar remover uma dependência que não existe mais (ex.: `groupId:artifactId` já removido por outra via) falha com erro claro; nenhuma escrita ocorre.

## Requisitos não funcionais

- Mesma garantia das fatias anteriores: o retorno é sempre uma re-inferência via `infer_structure`.
- Reaproveita `MavenPomWriter.remove_managed_dependency` sem nenhuma mudança — já testado e usado por `remove_module` desde a Fase 2.

## Dependências de outras features

- Depende de `phase-2-update-dependency` (mesmo painel, mesmo modelo `Dependency`).
- Depende de [[05-inferencia-de-projeto-existente]] (re-infere o estado após a remoção).

## Riscos / limitações conhecidas

- Remover uma entrada gerenciada da qual módulos dependem via dependência **direta** sem versão explícita deixa essas dependências sem versão resolvida — o Maven vai reclamar na próxima build (`Missing dependency version`). Esta fase não detecta nem avisa sobre esse caso (ao contrário de `remove_module`); documentado como limitação conhecida, não um bug.
- Se por algum motivo (fora do fluxo normal da TUI) a mesma `groupId:artifactId` estiver gerenciada em mais de um módulo, `remove_dependency` remove apenas a primeira ocorrência encontrada na varredura (mesma ordem de `_find_bom_module`/`_find_dependents`) — caso extremamente incomum, não coberto por teste dedicado.
