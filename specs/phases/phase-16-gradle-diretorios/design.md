# Fase 16 — Gradle: Diretórios — Design

## Por que diretórios primeiro

Das 11 mutações da interface `BuildToolAdapter`, `add_directory`/`remove_directory` são as únicas duas que, no `MavenAdapter`, **não tocam** `pom.xml` — olhando `MavenAdapter.add_directory`/`remove_directory`, o corpo inteiro é `_find_module` → `_resolve_module_relative_path` → `mkdir`/`rmdir`/`rmtree` → `infer_structure`, nenhuma chamada a `MavenPomWriter`. Isso é uma consequência direta de diretórios-padrão nunca precisarem de declaração explícita no `pom.xml` (só diretórios *customizados*, fora do padrão, precisam do `build-helper-maven-plugin` — `register_directory_role`, fora de escopo aqui).

O mesmo vale para Gradle: o plugin `java`/`java-library` reconhece `src/main/java` etc. por convenção, sem nada em `build.gradle(.kts)`. Logo, esta é a única mutação da lista que pode ser implementada **sem** resolver o problema em aberto mais arriscado da feature — editar Groovy/Kotlin como texto (mantendo formatação, indentação, e um subconjunto convencional coerente com o que o parser da Fase 15 já lê de volta). Fatias futuras (`add_module`, `update_dependency`, etc.) vão precisar desse "writer" Gradle; esta fatia não.

## Extração: `manager/adapters/common/lookup.py`

```
find_module(module: Module, name: str) -> Module | None
resolve_module_relative_path(project: Project, target: Module, relative_path: Path) -> Path
```

Ambas eram métodos privados de `MavenAdapter` (`_find_module`, `_resolve_module_relative_path`) — busca em profundidade na árvore de `Module` e resolução/validação de path relativo contra o diretório do módulo. Nenhuma das duas toca em nada específico de Maven (XML, `MavenPomWriter`, etc.); operam só sobre o modelo de domínio agnóstico. Mesmo padrão de reaproveitamento já aplicado a `detect_directory_structure` na Fase 15 (extraído de `maven/directory.py` para `common/directory.py`).

Para minimizar o diff em `MavenAdapter` (13 call sites de `self._find_module`/`self._resolve_module_relative_path` espalhados pelas outras mutações, todas fora do escopo desta fatia), os métodos privados permanecem como wrappers finos delegando para as funções de `common.lookup`, em vez de reescrever cada call site:

```python
def _find_module(self, module, name):
    return find_module(module, name)

def _resolve_module_relative_path(self, project, target, relative_path):
    return resolve_module_relative_path(project, target, relative_path)
```

Comportamento idêntico, zero regressão, e `GradleAdapter` importa as mesmas funções diretamente (sem indireção de instância).

## `GradleAdapter.add_directory`/`remove_directory`

Corpo idêntico ao `MavenAdapter`, usando `find_module`/`resolve_module_relative_path` de `common.lookup` e reaproveitando `DirectoryNotEmptyConflict` (já genérico em `adapters/base.py`, não específico de Maven). Nenhuma lógica nova: mesmos guards (módulo inexistente, path escaping, diretório já existe / não existe, diretório-raiz do módulo, não-vazio sem `force`).

## Impacto na camada Textual

Nenhum. `MainScreen.add_directory`/`remove_directory` (`screens/main_screen.py`) já chamam `self._adapter.add_directory`/`remove_directory` através da interface `BuildToolAdapter`, sem nenhuma ramificação por build tool — o mesmo código que já funciona para Maven passa a funcionar para Gradle assim que o método deixa de ser stub. Os bindings do Painel [5] (`n` diretório do checklist, `x` caminho livre, `d` remover) já eram genéricos desde a Fase 4/11.

## Testes

- `tests/test_gradle_adapter_add_directory.py` / `tests/test_gradle_adapter_remove_directory.py` — espelham `test_maven_adapter_add_directory.py`/`test_maven_adapter_remove_directory.py` caso a caso, rodando contra `tests/fixtures/gradle-multi-module-groovy/` em vez de `maven-multi-module`.
- `tests/test_gradle_adapter_stubs.py` — remove os dois casos (`add_directory`/`remove_directory` deixam de ser stub); os outros 9 continuam.
- Nenhum teste novo de `common/lookup.py` isolado — comportamento já é exercitado end-to-end pelos testes de `add_directory`/`remove_directory` de ambos os adapters (Maven pré-existente + Gradle novo).
