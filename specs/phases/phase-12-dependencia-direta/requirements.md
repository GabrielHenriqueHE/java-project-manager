# Fase 12 — Dependência Direta na TUI — Requirements

## Contexto

`MavenAdapter.update_dependency` (Fase 2) já faz upsert de dependência tanto gerenciada (`managed=True`, `dependencyManagement`) quanto direta (`managed=False`, `<dependencies>` do módulo) — o backend nunca teve essa limitação. A limitação é só na TUI: `DependencyFormScreen` sempre monta `Dependency(managed=True, ...)`, e só é aberta pelo Painel [4] BOM + DEPENDENCIAS, que só lista `project.managed_dependencies` (a lista de gerenciadas do projeto inteiro). Não existe hoje nenhum jeito de ver ou adicionar uma dependência **direta** de um módulo qualquer pela TUI.

## Objetivo desta fatia

Adicionar/editar (upsert) uma dependência direta do módulo atualmente selecionado (Painel [3]) pela TUI, e mostrar as dependências diretas já existentes desse módulo no Painel [4] — que já se chama "BOM + DEPENDÊNCIAS", cumprindo a segunda metade da própria promessa do nome.

## Fora de escopo

Remover uma dependência direta pela TUI (o backend `MavenPomWriter.remove_dependency` já existe e é usado internamente por `remove_module`, mas expor isso como uma operação de usuário fica para uma fatia futura — o pedido original foi só "adicionar/editar"). Selecionar/navegar a lista de diretas com o teclado (é uma lista somente-leitura nesta fatia, mesmo padrão do checklist do Painel [5] antes de virar navegável).

## Critérios de aceite

- Selecionar um módulo qualquer no Painel [3] (inclusive um com `packaging=jar`, que não pode ter dependência gerenciada) e pressionar `m` no Painel [4] abre um formulário de nova dependência **direta** desse módulo.
- Confirmar o formulário com groupId+artifactId (version opcional, diferente da gerenciada que exige version) grava a dependência em `<dependencies>` do módulo selecionado, não em `<dependencyManagement>`.
- Depois de confirmar, o Painel [4] passa a listar essa dependência numa seção "diretas de `<módulo>`", distinta da lista de gerenciadas (BOM) existente.
- O fluxo existente de adicionar dependência **gerenciada** via `n` (Painel [4]) continua idêntico — nenhuma regressão.
