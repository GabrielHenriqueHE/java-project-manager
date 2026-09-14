# Fase 2 — Adicionar Módulo — Design

## `xml_utils.append_with_matching_indent`

Helper genérico (usado por `add_module_entry` e reaproveitável para futuras inserções, ex.: novas `<dependency>` em `update_dependency`): anexa um novo elemento filho a um container, reproduzindo o padrão de indentação (`tail`/`text`) já usado pelos filhos existentes — ou, se o container estiver vazio, reaproveita o `text` de abertura do próprio container.

## `MavenPomWriter`

- `add_module_entry(pom_path, module_value)` — insere `<module>module_value</module>` ao final de `<modules>` existente, via `append_with_matching_indent`. Retorna `False` (sem tocar no arquivo) se `<modules>` não existir ou se a entrada já estiver presente (idempotente).
- `create_pom(pom_path, *, parent_group_id, parent_artifact_id, parent_version, artifact_id, group_id=None, version=None, packaging="jar", name=None, description=None, dependencies=None)` — monta um `pom.xml` novo do zero via construção programática de elementos lxml (nunca por interpolação de string, para que caracteres especiais como `&` sejam escapados corretamente pelo serializador). Usa `etree.indent(tree, space="  ")` para uma formatação limpa. `dependencies` é particionado em `managed` (vai para `<dependencyManagement><dependencies>`) e diretas (vão para `<dependencies>`), usando o mesmo flag `Dependency.managed` do modelo de domínio.

## `MavenAdapter.add_module`

Fluxo (`src/manager/adapters/maven/adapter.py`):

1. Resolve o módulo pai: `project.root_module` se `parent_name` for `None`, senão busca via `_find_module` (reaproveitado de `remove_module`); erro claro se não encontrado.
2. Valida `parent.metadata.packaging == "pom"` — só agregadores podem receber novos módulos.
3. Valida que não existe outro módulo com o mesmo nome (`_find_module` no projeto inteiro) e que o diretório de destino (`parent_dir / artifact_id`) ainda não existe em disco.
4. Decide `group_id`/`version` explícitos apenas quando divergem dos valores do pai — caso contrário ficam `None` e o filho herda via `<parent>` (convenção Maven idiomática, evita redundância).
5. Chama `writer.create_pom(...)` — **isso acontece antes de tocar no pom do pai**, para que uma falha aqui nunca deixe o pom do pai referenciando um módulo inexistente.
6. Cria os diretórios padrão: união de `source_dirs`/`test_dirs`/`resource_dirs`/`test_resource_dirs` do `DirectoryStructure` do módulo rascunho (por padrão, os 4 diretórios `maven-standard`).
7. Só então chama `writer.add_module_entry(parent_pom, artifact_id)`; se retornar `False` (pom do pai sem `<modules>`), levanta `ValueError` — o diretório/pom do filho já foram criados nesse ponto (aceitável: ficam "órfãos" no disco, não registrados em nenhum pom, mas nada foi corrompido; o usuário pode apagá-los manualmente ou o adapter pode detectar/reaproveitar esse diretório numa tentativa futura, já que `module_dir.exists()` passaria a barrar uma nova tentativa com o mesmo nome).
8. Retorna `self.infer_structure(root_path)`.

O valor escrito em `<module>` é sempre `artifact_id` (nome do diretório == artifactId, mesma convenção usada em toda a árvore inferida e em `remove_module`).

## TUI

- `ModuleFormScreen` (`src/manager/screens/widgets/module_form.py`, novo): `ModalScreen[Module | None]` com campos artifactId (obrigatório), groupId, version, packaging (default "jar"), name, description. Confirmar monta um `Module` "rascunho" (apenas `metadata` é significativo; `relative_path`/`build_file` são placeholders exigidos pelo schema Pydantic mas ignorados pelo adapter, que recalcula tudo via `infer_structure`) e faz `dismiss(module)`; cancelar faz `dismiss(None)`.
- `ProjectDetailScreen` ganha o binding `a` → `action_add_module`, que usa `self._selected_module` (o módulo atualmente destacado na árvore) como pai, resolve o adapter via `detect_adapter` (mesmo serviço já usado no resto do app) e trata `ValueError` do adapter via `self.notify(..., severity="error")`.
- `_apply_updated_project` (já existente, criado para `remove_module`) foi generalizado para receber a mensagem de notificação (`message="Modulo removido"` vs. `message=f"Modulo '{module.name}' criado"`), evitando duplicar a lógica de "reconstruir árvore + mostrar módulo raiz".

## Casos de borda tratados

- Pai sem `<modules>`: erro claro, nada é escrito no pom do pai (o filho pode já ter sido criado em disco — ver passo 7 acima).
- Nome duplicado: barrado antes de qualquer escrita.
- Diretório já existente (órfão, não registrado em nenhum pom): barrado antes de qualquer escrita.
- groupId/version iguais ao do pai: omitidos do pom filho (herança implícita).
- Caracteres especiais em `name`/`description` (ex.: `&`): escapados corretamente pela construção programática de elementos lxml.
