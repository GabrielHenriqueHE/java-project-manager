# Fase 6 — Criar Projeto a Partir de Manifesto — Requirements

Primeira fatia de [[01-gerenciamento-de-projetos]]: até aqui, todo módulo, dependência ou diretório só pode ser adicionado a um projeto **já existente**, um de cada vez, pela TUI (`add_module`, `add_directory`, `update_dependency`, etc.). Não existe nenhum caminho para nascer um projeto Java multi-módulo do zero — o usuário precisaria criar manualmente o pom raiz e depois repetir `add_module`/`add_directory`/`register_directory_role`/`update_dependency` módulo por módulo. Esta fatia fecha essa lacuna: o usuário descreve a estrutura completa desejada (módulos, BOM, dependências, diretórios) num arquivo de manifesto YAML e a ferramenta materializa tudo de uma vez, reaproveitando as mutações do adapter já existentes.

Decisão #4 do decision log (`00-overview.md`: "Sem manifesto próprio de projeto") trata exclusivamente de **persistência de estado de projetos já existentes/gerenciados** — a ferramenta nunca guarda módulos/dependências/diretórios num manifesto próprio como fonte de verdade contínua; esse estado é sempre re-derivado ao vivo via `infer_structure()`. O manifesto desta fatia é um conceito diferente: **entrada efêmera**, consumida uma única vez no momento da criação. Depois de materializado, o projeto passa a ser regido normalmente pela decisão #4 (nenhum vínculo com o arquivo de manifesto original é mantido; uma segunda leitura do mesmo projeto usa `infer_structure()` como qualquer outro projeto). Não reabre a decisão.

## Escopo

**Dentro:**
- Um schema de manifesto em YAML, espelhando o modelo de domínio já existente (`Project`/`Module`/`Dependency`/`DirectoryStructure` em `src/manager/models.py`) — mas **sem** os campos que hoje são sempre derivados (`relative_path`, `build_file`), já que esses só fazem sentido depois que o projeto existe em disco.
- Um módulo filho no manifesto pode omitir `group_id`/`version` para herdar do módulo pai — mesmo comportamento já usado em `add_module`/`update_metadata` (`src/manager/adapters/maven/adapter.py`), não uma regra nova.
- Um módulo do manifesto pode ser marcado como BOM (`packaging: pom` + `dependencyManagement`) — suporte incluído já nesta fatia, e não adiado, porque gerenciar dependências via BOM é o caso de uso mais central do produto (ver "Problema" em `00-overview.md`); um fluxo de criação de projeto que não permite nascer já com BOM cobriria mal esse caso de uso principal.
- `BuildToolAdapter` ganha um novo método (ex.: `create_project(manifest, destination_path) -> Project`) que lê o manifesto, valida a árvore inteira e materializa em disco chamando as mutações já existentes do adapter concreto (equivalente Maven de `create_pom`, `add_module`, `add_directory`, `register_directory_role`, `update_dependency`).
- Validação de árvore completa **antes** de qualquer escrita em disco: nomes de módulo duplicados, referências de dependência quebradas, campos obrigatórios ausentes — mesmo padrão "erro claro, nenhuma escrita" já usado em `add_module`/`add_directory`.
- `destination_path` precisa estar vazio ou não existir ainda — evita sobrescrever um projeto já presente.
- TUI: novo fluxo (formulário com caminho do manifesto + diretório de destino) que chama `create_project` e, em sucesso, abre o projeto recém-criado (mesmo padrão de `set_project` usado após as outras mutações).

**Fora (fatias futuras ou fora do produto):**
- Clone remoto (`git clone` + inferir o projeto clonado) — citado no mesmo bullet de roadmap original (`00-overview.md`), mas é uma fatia distinta (não depende de manifesto nenhum, depende só de `infer_structure` sobre o resultado do clone).
- Editar o manifesto pela própria TUI (formulário visual para montar a árvore) — esta fatia só lê e consome um arquivo de manifesto já escrito à mão pelo usuário em outro editor.
- Templates reutilizáveis / catálogo de manifestos prontos (ex.: "novo projeto Spring Boot") — esta fatia cobre só a leitura de um manifesto arbitrário fornecido pelo usuário, não uma biblioteca de manifestos pré-definidos.
- Suporte a outras build tools além de Maven nesta fatia (o método entra na interface `BuildToolAdapter` para o contrato ficar pronto para uma futura `GradleAdapter`, mas só `MavenAdapter` implementa de fato).

## User stories

- Como desenvolvedor Java, quero descrever a estrutura completa de um projeto multi-módulo (incluindo módulos, BOM e dependências) num arquivo YAML e pedir para a ferramenta materializá-la de uma vez, em vez de criar módulo por módulo manualmente pela TUI.

## Critérios de aceite

- Um manifesto válido com múltiplos módulos e um módulo BOM materializa a árvore completa (poms, diretórios convencionais, dependências diretas e gerenciadas) de forma equivalente ao que `infer_structure()` reproduziria ao ler o resultado de volta.
- Um módulo filho sem `group_id`/`version` no manifesto herda do pai no pom gerado (sem repetir o valor herdado), mesma regra de `add_module`.
- Um manifesto com nome de módulo duplicado, referência de dependência para um módulo inexistente, ou campo obrigatório ausente falha com mensagem clara **antes** de qualquer escrita em disco.
- Tentar criar num `destination_path` que já existe e não está vazio falha com erro claro, nenhuma escrita.
- O projeto criado não mantém nenhum vínculo com o arquivo de manifesto original — reabrir esse projeto depois usa `infer_structure()` normalmente, como qualquer outro projeto gerenciado.

## Requisitos não funcionais

- Mesma garantia das fatias anteriores de mutação: em sucesso, retorna sempre o `Project` re-inferido via `infer_structure()` do diretório recém-criado (não um `Project` montado manualmente a partir do manifesto), para garantir que o que a ferramenta reporta é sempre o que está de fato em disco.
- Reaproveita a lógica de criação de diretórios já usada em `add_module` (conjunto de diretórios de `directory_structure` criados com `mkdir(parents=True, exist_ok=True)`), sem duplicar essa lógica para o módulo raiz.

## Dependências de outras features

- Depende de [[04-estrutura-de-diretorios]] (criação de diretórios) e [[05-inferencia-de-projeto-existente]] (o retorno de `create_project` é sempre via `infer_structure`).
- Depende de estender `MavenPomWriter.create_pom` para aceitar um `parent` opcional — hoje esse método sempre escreve `<parent>`, porque é usado só por `add_module` (módulo novo dentro de um projeto já existente); o pom raiz de um projeto novo não tem `<parent>` nenhum. Fica marcado como detalhe de design/risco desta fatia, não decidido em detalhe neste requirements.

## Riscos / limitações conhecidas

- O manifesto corre o risco de virar um "segundo modelo de domínio" que precisa evoluir em sincronia com `src/manager/models.py` sempre que o domínio mudar. Mitigado por reaproveitar os mesmos tipos Pydantic do domínio (um subconjunto de campos, não uma estrutura paralela inventada do zero).
- Estender `create_pom` para parent opcional toca um método já usado e testado por `add_module` — risco de regressão nesse fluxo existente; a fatia de design/implementação precisa garantir cobertura de teste equivalente para os dois casos (com e sem parent).
- Validar a árvore inteira antes de escrever exige que a validação replique regras que hoje só existem espalhadas nos métodos de mutação individuais (ex.: "parent precisa ter packaging pom" em `add_module`) — risco de as duas validações divergirem com o tempo se não forem centralizadas/reaproveitadas.
