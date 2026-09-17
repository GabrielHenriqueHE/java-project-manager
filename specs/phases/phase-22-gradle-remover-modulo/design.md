# Fase 22 — Gradle: Remover Módulo — Design

## `remove_include`

Inverso simétrico de `add_include` (Fase 21): varre todas as declarações `include(...)` do arquivo (`INCLUDE_RE.finditer`, não só a primeira — mais robusto que `add_include`, que só olha a primeira, já que aqui precisamos *achar* onde a entrada está, não decidir onde inserir uma nova) até achar uma cuja lista contenha `artifact_id`; remove só essa entrada da lista (recompondo com as aspas do dialeto) ou a declaração inteira se for a única. Retorna `False` sem tocar em nada se não achar em nenhuma declaração.

## `GradleAdapter.remove_module`

Estrutura idêntica ao `MavenAdapter.remove_module`, usando as funções de `common/lookup` já extraídas na Fase 17 (`find_parent`, `find_dependents`, `find_bom_module`) e o par de métodos de remoção de dependência já existentes (`remove_managed_dependency` da Fase 19, `remove_dependency` — direta — da Fase 20):

1. `find_module`/`find_parent` guards (módulo inexistente / é a raiz).
2. `find_dependents` + `DependentModuleConflict` se houver e `force=False`.
3. `remove_include` no `settings.gradle(.kts)` — como o Maven, o resultado (`bool`) não é checado; a árvore em memória já não terá mais o módulo de qualquer forma, e uma entrada de `include` ausente por algum motivo não é um erro fatal aqui.
4. `find_bom_module` + `remove_managed_dependency` se existir um BOM diferente do próprio módulo removido.
5. `remove_dependency` (direta) em cada dependente.

Igual ao Maven, **não remove o diretório do módulo em disco** — só desregistra a estrutura (arquivo de build + entradas de dependência). Removê-lo fisicamente é responsabilidade de `remove_directory` (Fase 16), separado por design desde o início do produto.

## Bug corrigido: `_FULL_DEP_LINE_RE` vazando entre linhas

Ao escrever os testes desta fase (o primeiro cenário real com **duas** dependências no mesmo bloco sendo buscadas *por conteúdo*, não só "a única que existe"), apareceu um bug latente: a cauda do regex (`\s*\)?\s*\)?[ \t]*\n?`) usava `\s*` — que casa `\n` — antes dos parênteses de fechamento opcionais. Num bloco com duas linhas, o primeiro match consumia o `\n` e toda a indentação da linha seguinte, deixando o motor de regex no meio da segunda linha (logo antes do `api`) sem um `\n` imediatamente anterior — e como a busca usa `^` (âncora de início de linha, `re.MULTILINE`), a segunda entrada nunca conseguia começar um match novo dali. Resultado prático: `remove_managed_dependency`/`remove_dependency`/`upsert_dependency` só enxergavam a **primeira** entrada de um bloco com 2+ linhas, silenciosamente falhando (retornando "não encontrado") para qualquer coordenada que fosse a segunda em diante.

Como nenhum teste das Fases 18-20 exercitava buscar especificamente a *segunda* entrada de um bloco com múltiplas linhas (cada teste ou tinha uma única entrada relevante, ou removia todas em sequência, sempre acertando "a que sobrou por último" por acidente), o bug não tinha superfície ainda. Corrigido trocando os dois `\s*` da cauda por `[ \t]*` — só espaço/tab da mesma linha, nunca atravessando `\n`. Nenhuma outra fase precisou de mudança: a correção é só na regex compartilhada, usada por `_upsert_dep_line_in_text`/`_remove_dep_line` desde a Fase 18.

## Testes

`tests/test_gradle_adapter_remove_module.py`: remoção sem dependentes (ambos os dialetos), não apaga o diretório, conflito de dependentes sem `force`, `force=True` remove a dependência direta do dependente E a entrada gerenciada do BOM (este último é justamente o caso que expôs o bug do regex, já que `bom` tem duas entradas em `constraints{}` e a removida por `remove_module` é a segunda, `com.example:core`), `settings.gradle` atualizado em disco, módulo/raiz inexistente ou raiz rejeitados, resultado batendo com reinferência.
