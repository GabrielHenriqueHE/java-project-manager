# Fase 25 — Duplicar Módulo — Design

## `copy_module_tree` (`adapters/common/copy.py`)

Único utilitário genérico de cópia de árvore introduzido nesta fase:
`shutil.copytree(source_dir, dest_dir, ignore=...)`, ignorando saída de
build/VCS/IDE conhecida (`target`, `build`, `bin`, `.gradle`, `out`, `.git`,
`.idea`). Os três `shutil.copytree` já existentes no código
(`_materialize_directories` em ambos adapters, `export_source_files` em
`manifest.py`) copiam *por diretório de papel* (`source_dirs`/`test_dirs`/…)
com fallback para `mkdir` quando a origem não existe — um padrão
genuinamente diferente de "copiar a árvore inteira do módulo de uma vez", por
isso não foram unificados com este helper. `duplicate_module` é o primeiro
caso que precisa copiar o módulo inteiro (incluindo o arquivo de build) de
uma vez, e os dois adapters fazem exatamente essa chamada — daí valer a
extração.

## `GradleAdapter.duplicate_module`

Estrutura idêntica a `add_module`/`remove_module` (guards via `find_module`,
`find_settings_file`): valida módulo fonte (existe, sem submódulos), valida
`parent_name` com a mesma regra de `add_module` (só `None` ou a própria raiz
— a árvore Gradle é achatada desde a Fase 15), valida nome/diretório de
destino livres, copia a árvore com `copy_module_tree`, registra via
`GradleWriter.add_include` (Fase 21). Nenhuma edição de conteúdo do
`build.gradle(.kts)` copiado é necessária: Gradle não tem `artifactId` dentro
do arquivo (a identidade é o nome do `include(...)`), e o dialeto
Groovy/Kotlin é preservado automaticamente por ser cópia literal — mais
simples que `add_module`, que precisa *derivar* o dialeto do
`settings.gradle(.kts)` para saber qual arquivo gerar do zero.

Override de `group_id`/`version`, quando informado, é aplicado **depois** da
cópia+registro, chamando `self.update_metadata(result, new_module_name, ...)`
sobre o `Project` já reinferido — reaproveita a mutação existente (Fase 17)
em vez de duplicar lógica de escrita de `group`/`version` no
`build.gradle(.kts)`.

## `MavenAdapter.duplicate_module`

Mesma estrutura de guards que `add_module` (`_find_module`, packaging do pai
precisa ser `pom`, nome/diretório livres), com uma diferença de default:
`parent_name=None` aqui usa o **mesmo pai do módulo fonte** (`_find_parent`),
não a raiz — duplicar cria um irmão por padrão, que é o caso motivador real
(copiar A para virar B no mesmo agregador). Um `parent_name` explícito
segue a mesma regra de `add_module` (precisa existir e ter `packaging=pom`).

Depois de `copy_module_tree`, dois ajustes pontuais no `pom.xml` copiado:

1. `MavenPomWriter.set_artifact_id` — sempre, batiza a cópia com
   `new_module_name` (o `pom.xml` copiado ainda tem o `artifactId` do
   módulo fonte).
2. `MavenPomWriter.set_parent` — **só quando `reparenting` é verdadeiro**
   (`original_parent.relative_path != parent.relative_path`, incluindo o
   caso de o fonte ser a própria raiz sem pai). No caminho default
   (duplicar como irmão), o `<parent>` copiado já é idêntico ao que o novo
   módulo precisa, e fica intocado — zero escrita extra no caso motivador
   real. Só quando `parent_name` move o módulo para um agregador diferente
   é que o `<parent>` copiado (que ainda referencia o GAV do pai antigo)
   precisa ser reescrito para apontar para o novo pai.

`set_artifact_id`/`set_parent` são primitives **novos**, não expostos via
`update_metadata` (que continua recusando renomear `artifactId` de um módulo
já existente, decisão da Feature 03 mantida intacta) — aqui o módulo acabou
de nascer via cópia, não está sendo renomeado.

Override de `group_id`/`version` segue o mesmo caminho do Gradle: aplicado
depois, via `self.update_metadata(...)` sobre o resultado já reinferido.

## Formulário e TUI

`DuplicateModuleFormScreen` (novo) — mesmo padrão visual de `ModuleFormScreen`,
mas devolve um `dict` em vez de um `Module` rascunho (não faz sentido montar
um `Module` completo aqui: `duplicate_module` só precisa de três strings, e
o restante do módulo vem da cópia real em disco). Campo `new_name`
obrigatório; `group_id`/`version` opcionais, deixados em branco herdam do
fonte (decisão confirmada com o usuário — a alternativa de sempre herdar sem
nunca pedir override foi descartada porque o usuário quis poder fixar
group/version na hora, mantendo o comportamento de herdar como default
quando os campos ficam vazios).

`ModulesPanel` ganha o binding `c` ("copiar") — `d` já é `remove_module`,
`n` já é `add_module`.

## Testes

- `tests/test_adapters_common_copy.py`: `copy_module_tree` copia
  recursivamente e ignora os diretórios de saída de build/VCS/IDE
  conhecidos.
- `tests/test_maven_pom_writer_set_artifact_id.py` /
  `tests/test_maven_pom_writer_set_parent.py`: os dois primitives novos,
  isolados do adapter.
- `tests/test_maven_adapter_duplicate_module.py`: cópia+registro como
  irmão (conteúdo de arquivo preservado, dependências preservadas,
  `group_id`/`version` herdados), `artifactId` correto, `parent_name`
  explícito igual ao original (sem reescrita de `<parent>`), `parent_name`
  diferente com reescrita de `<parent>` (usa um agregador secundário
  construído no próprio teste, já que nenhum módulo do fixture padrão tem
  `<modules>` pré-existente fora da raiz), override de `group_id`/`version`,
  validações negativas (nome duplicado, diretório existente, fonte
  inexistente/com submódulos, pai desconhecido/não-`pom`), resultado batendo
  com reinferência.
- `tests/test_gradle_adapter_duplicate_module.py`: equivalente nos dois
  dialetos (Groovy/Kotlin), incluindo preservação do plugin customizado
  (`java-library`) no `build.gradle` copiado — coisa que `add_module`
  *não* preserva, por regenerar o arquivo do zero — e rejeição de
  `parent_name` não-raiz.
