# Fase 13 — Clonar Repositório Remoto — Requirements

## Contexto

`specs/features/01-gerenciamento-de-projetos/requirements.md` já listava "clonar/baixar projetos de um repositório remoto" como fora de escopo da Fase 1, adiado para uma fase futura. Hoje o único jeito de registrar um projeto é apontar para um path já existente em disco (`ImportProjectScreen`, Painel [1] `n`) — se o repositório só existe remotamente, o usuário precisa clonar manualmente num terminal antes de importar.

## Objetivo desta fatia

Clonar um repositório remoto via `git clone` para um path local e, em caso de sucesso, aplicar o mesmo fluxo de registro já usado por `ImportProjectScreen` (detectar build tool, inferir estrutura, `ProjectRegistry.add`).

## Escopo

**Dentro:**
- `git clone <url> <destino>` via `subprocess`, sem dependência Python nova (git já é uma ferramenta de sistema esperada, no mesmo espírito de como o projeto já lida com Maven só manipulando `pom.xml`, nunca invocando `mvn`).
- Novo binding no Painel [1] PROJETOS que abre um formulário com dois campos: URL do repositório e path de destino.
- Reaproveitar a mesma detecção/inferência/registro de `ImportProjectScreen` após o clone bem-sucedido.

**Fora:**
- Autenticação especial (SSH agent, token, etc.) — delegado inteiramente ao `git` do sistema, que já resolve isso via suas próprias configurações (`~/.ssh`, credential helper). A ferramenta não guarda nem pede credenciais.
- Clonar um branch/tag específico, profundidade rasa (`--depth`), ou qualquer opção avançada de `git clone` — só a forma mais simples (`git clone <url> <destino>`), podendo crescer numa fatia futura se pedido.

## Critérios de aceite

- Dado um repositório remoto acessível (ex.: URL local de teste ou HTTPS), quando o usuário informa URL + destino e confirma, então o repositório é clonado para o destino, a build tool é detectada, e o projeto aparece registrado — mesmo resultado final de `ImportProjectScreen` num path já existente.
- Dado um destino que já existe e não está vazio, quando confirmado, então nada é clonado e uma mensagem de erro clara aparece — sem sobrescrever o que já existia ali.
- Dado que o `git` não está instalado no sistema, quando confirmado, então uma mensagem de erro clara aparece (não uma exceção não tratada / crash da TUI).
- Dado uma URL inválida ou inacessível, quando confirmado, então a mensagem de erro do próprio `git` (stderr) é mostrada ao usuário, para diagnóstico.
- Dado um clone bem-sucedido de um repositório que não é um projeto Java reconhecível, quando a detecção falha, então os arquivos clonados permanecem no disco (nada é desfeito), mas nada é adicionado ao registry, e o usuário vê uma mensagem explicando o que aconteceu.
