# Fase 4 — Estrutura de Diretórios — Requirements

Primeira fatia de mutação sobre [[04-estrutura-de-diretorios]]: até aqui a feature só cobria inferência/visualização (Fase 1) — o Painel [5] ESTRUTURA mostra um checklist de 8 diretórios convencionais, mas marcá-los como ausentes não fazia nada além de informar. Esta fatia torna o checklist acionável: criar em disco qualquer um dos diretórios do checklist que ainda não existe para o módulo ativo.

## Escopo

**Dentro:**
- `BuildToolAdapter.add_directory(project, module_name, relative_path)` novo método na interface: cria `relative_path` (relativo à raiz do módulo) em disco, com os diretórios intermediários necessários, e devolve o projeto re-inferido.
- `MavenAdapter.add_directory`: mesma operação — para Maven, criar uma pasta não exige tocar no `pom.xml` (diferente de módulos/dependências), então a implementação é só I/O de filesystem validado.
- Validações: módulo precisa existir; `relative_path` não pode já existir em disco; `relative_path` não pode escapar do diretório do módulo (proteção contra `..`/paths absolutos vindos de qualquer chamador, já que esta operação grava no disco a partir de um valor que em tese vem de input do usuário).
- Wiring na TUI: Painel [5] (`StructurePanel`) ganha navegação (`j`/`k`) sobre os itens do checklist do módulo ativo (`space` continua alternando qual módulo está ativo) e `enter` cria o item destacado, se ausente; se já existir, apenas notifica sem re-escrever nada.
- O conjunto de diretórios criáveis nesta fatia é exatamente o checklist já existente (`_CHECKLIST_DIRS`: os 4 padrão Maven + `src/main/webapp`, `src/main/proto`, `src/it/java`, `docs`) — nenhum caminho livre digitado pelo usuário.

**Fora (fatias futuras):**
- Caminho de diretório livre/digitado pelo usuário (formulário com `Input` de texto) — esta fatia só ativa os 8 itens já visualizados; um editor verdadeiramente "customizado" (qualquer caminho, qualquer `role`) fica para depois.
- Atribuir/editar `DirectoryNode.role` do diretório criado — o modelo tem o campo, mas esta fatia não expõe escolha de papel na TUI.
- Remover diretórios — ação destrutiva de maior risco, fora de escopo.
- Registrar o diretório no `pom.xml` (ex.: `build-helper-maven-plugin` para fontes extras como `src/main/proto`, ou plugins de `war`/`webapp`) — a operação cria só a pasta; qualquer wiring de build necessário para a build tool reconhecer a pasta fica fora.
- Criar arquivos placeholder dentro do diretório novo (ex.: `.gitkeep`) — diretório vazio é aceitável.

## User stories

- Como desenvolvedor Java, quero criar rapidamente um diretório de estrutura padrão (ex.: `src/main/resources`) que falta num módulo, sem sair da TUI para rodar `mkdir`.

## Critérios de aceite

- Navegar até um item do checklist marcado como ausente (`[ ]`) e pressionar `enter` cria o diretório em disco e o checklist passa a mostrar `[x]` após o refresh.
- Repetir a mesma ação num item já marcado (`[x]`) não falha, não altera nada em disco, e mostra uma notificação informando que o diretório já existe.
- A criação usa `mkdir(parents=True)` — criar `src/main/webapp` num módulo que ainda nem tem a pasta `src/main` funciona numa única ação.
- Tentar chamar `add_directory` com um `relative_path` que escaparia do diretório do módulo (ex.: `../../etc`) falha com erro claro; nada é criado.
- Tentar chamar `add_directory` para um módulo inexistente falha com erro claro.

## Requisitos não funcionais

- Mesma garantia das fatias de mutação anteriores: o retorno é sempre uma re-inferência via `infer_structure` (ver [[05-inferencia-de-projeto-existente]]), nunca um `Project`/`Module` remontado em memória.
- A validação de path traversal roda antes de qualquer `mkdir`, para nunca criar nada fora do módulo mesmo em caso de bug de chamada.

## Dependências de outras features

- Depende de [[05-inferencia-de-projeto-existente]] (re-infere o estado após a criação; `detect_directory_structure` já existente decide se o módulo continua `maven-standard` ou vira `custom` após a nova pasta aparecer).
- Consumida por [[04-estrutura-de-diretorios]] — fecha parcialmente o "Fora" que a Fase 1 dessa feature deixou registrado ("aplicação automática (criação de pastas em disco)").

## Riscos / limitações conhecidas

- Criar uma pasta não-padrão sob `src/` (ex.: `src/it/java`) faz `detect_directory_structure` reclassificar o módulo inteiro como `convention="custom"` na próxima inferência (comportamento já existente da função, não alterado nesta fatia) — os campos `source_dirs`/`resource_dirs`/etc. do módulo passam a ficar vazios (a árvore genérica em `tree` assume). Isso é uma limitação conhecida e pré-existente de `detect_directory_structure`, não introduzida aqui.
