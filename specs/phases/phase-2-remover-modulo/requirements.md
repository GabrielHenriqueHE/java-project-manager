# Fase 2 — Remover Módulo — Requirements

Primeira fatia de mutação real sobre [[03-gerenciamento-de-modulos]]: implementar `remove_module` de ponta a ponta (Maven), tanto no adapter quanto na TUI. `add_module` e `update_dependency`/`update_metadata` ficam para fatias seguintes da Fase 2.

## Escopo

**Dentro:**
- `MavenAdapter.remove_module(project, module_name, force=False)` funcional: remove a entrada `<module>` do pom pai direto do módulo, a entrada gerenciada no módulo BOM (se houver), e as `<dependency>` dos módulos dependentes.
- Detecção de dependentes via `DependentModuleConflict` quando `force=False` e existirem módulos que dependem do alvo.
- Guarda contra remoção do módulo raiz.
- Wiring na TUI: `ProjectDetailScreen` permite selecionar um módulo na árvore e remover (`r`); em caso de conflito, mostra `ConfirmModal` listando os dependentes antes de aplicar com `force=True`.

**Fora (fatias seguintes da Fase 2):**
- `add_module`, `update_dependency`, `update_metadata`.
- Apagar o diretório do módulo do disco — `remove_module` apenas desregistra o módulo da build (pom pai/BOM/dependentes); os arquivos de código-fonte do módulo permanecem intactos. Apagar arquivos é uma ação destrutiva de maior risco, fora do escopo desta fatia.

## User stories

- Como desenvolvedor Java, quero remover um módulo que ninguém mais usa e ter o pom pai atualizado automaticamente.
- Como desenvolvedor Java, quero ser avisado antes de remover um módulo do qual outros módulos dependem, para decidir conscientemente se quero remover essas dependências também.

## Critérios de aceite

- Remover um módulo sem dependentes atualiza o pom pai (remove `<module>`) e o BOM (remove a entrada gerenciada, se houver) sem exigir confirmação extra.
- Remover um módulo com dependentes, sem `force`, levanta `DependentModuleConflict` listando os nomes dos módulos dependentes e não altera nenhum arquivo em disco.
- Repetir a mesma remoção com `force=True` remove também as `<dependency>` correspondentes dos módulos dependentes.
- Tentar remover o módulo raiz falha com um erro claro.
- Tentar remover um módulo inexistente falha com um erro claro.
- Na TUI, o fluxo de conflito mostra um modal de confirmação; cancelar não altera nada; confirmar aplica a remoção forçada e atualiza a árvore exibida.

## Requisitos não funcionais

- Nenhuma mutação deve corromper partes do `pom.xml` não relacionadas à operação (preservar indentação/comentários fora do escopo da mudança, na medida do que o parser XML permite).
- Após qualquer mutação, o estado em memória (`Project` retornado) deve corresponder exatamente a uma nova chamada de `infer_structure` sobre o disco (sem manifesto próprio, ver [[00-overview]]).

## Dependências de outras features

- Depende de [[05-inferencia-de-projeto-existente]] (precisa do estado atual antes de mutar, e usa `infer_structure` para devolver o estado pós-mutação).

## Riscos / limitações conhecidas

- lxml sempre serializa a declaração XML com aspas simples; normalizamos manualmente para aspas duplas para reduzir ruído no diff, mas a formatação da tag de abertura `<project ...>` com atributos multi-linha é colapsada para uma única linha pelo serializador (limitação do lxml/libxml2, não corrigida nesta fase).
