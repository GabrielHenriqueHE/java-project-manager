# Fase 25 — Duplicar Módulo — Requirements

Nova fatia de [[03-gerenciamento-de-modulos]], implementada simultaneamente em
`MavenAdapter` e `GradleAdapter` (diferente das fatias 16-23, que eram o
`GradleAdapter` alcançando paridade com um Maven já completo — aqui a
capacidade é nova nos dois ao mesmo tempo).

## Motivação

Caso real relatado pelo usuário: um projeto com módulos A e B precisou,
excepcionalmente, ter toda a estrutura de A copiada para B para depois podar
manualmente o que B não usaria — forma de segregar responsabilidades entre
módulos sem reescrever tudo do zero. Hoje o projeto não automatiza esse passo:
`add_module` só cria diretórios vazios; `create_project`/`export_source_files`
copiam de/para fora da árvore do projeto, nunca módulo→módulo dentro dela.

## Escopo desta fatia

**Dentro:**
- `BuildToolAdapter.duplicate_module(project, source_module_name, new_module_name, *, parent_name=None, group_id=None, version=None)`: copia a árvore de arquivos inteira do módulo fonte (código-fonte, resources, e o próprio arquivo de build) para um novo módulo, e registra esse novo módulo no build file do pai — igual a `add_module`, mas usando um módulo real como template em vez de materializar diretórios vazios.
- `parent_name=None` (default) cria o novo módulo como **irmão** do módulo fonte (mesmo pai); um `parent_name` explícito segue as mesmas regras de `add_module` por build tool.
- `group_id`/`version` opcionais: se omitidos, o novo módulo herda exatamente o que o módulo fonte tinha; se informados, sobrescrevem só o novo módulo (reaproveitando `update_metadata` já existente).
- Novo utilitário compartilhado `adapters/common/copy.py::copy_module_tree`, usado pelos dois adapters.
- Maven: dois novos writer primitives em `MavenPomWriter` — `set_artifact_id` (batiza a cópia) e `set_parent` (corrige `<parent>` só quando o novo módulo é reparentado para um pai diferente do original).
- TUI: novo modal `DuplicateModuleFormScreen`, `MainScreen.duplicate_module`, binding `c` ("copiar") no painel MÓDULOS `[3]`.

**Fora (mesma fronteira já declarada para `add_module`/`create_project`):**
- Rewrite de conteúdo Java/Kotlin (pacotes, imports, nomes de classe) dentro dos arquivos copiados.
- Poda seletiva de arquivos dentro da cópia — trabalho manual do usuário depois, por design.
- Duplicar um módulo com submódulos (árvores aninhadas) — mesma fronteira de `add_module`/`create_project`.

## Critérios de aceite

- Dado um módulo fonte sem submódulos, `duplicate_module` cria o novo módulo como cópia literal (incluindo o arquivo de build, preservando plugins/configuração customizada), registrado no build file do pai, visível numa reinferência.
- Sem `group_id`/`version` informados, o novo módulo herda exatamente o que o fonte tinha.
- Com `group_id`/`version` informados, só o novo módulo é afetado (módulo fonte intocado).
- `parent_name` explícito igual ao pai original não reescreve o bloco `<parent>` do pom copiado (Maven). `parent_name` explícito diferente reescreve `<parent>` para apontar para o novo pai.
- Levanta `ValueError` para: módulo fonte inexistente; módulo fonte com submódulos; nome do novo módulo já existente ou igual ao fonte; diretório de destino já existente; `parent_name` inválido (mesmas regras de `add_module` por build tool).

## Edge case conhecido, não corrigido nesta fase

Se o módulo fonte for o BOM do projeto (`is_bom=True`), a cópia também terá
`packaging="pom"` e as mesmas `managed_dependencies`, produzindo dois módulos
com `is_bom=True` após a reinferência. `find_bom_module` (busca em
profundidade, primeiro match) escolheria um dos dois implicitamente para
mutações que dependem dele (`remove_module`, `remove_dependency`). Risco já
documentado como pergunta em aberto em
`specs/features/03-gerenciamento-de-modulos/requirements.md` (heurística de
"qual é o BOM") — não uma regressão desta fase.

## Definição de pronto

`uv run pytest` verde, incluindo os novos arquivos de teste desta fase.
