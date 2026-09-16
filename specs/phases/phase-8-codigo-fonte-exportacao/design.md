# Fase 8 — Código-Fonte na Exportação — Design

## `src/manager/manifest.py` — nova função `export_source_files`

```python
import fnmatch
import shutil

def export_source_files(project: Project, manifest_path: Path, pattern: str) -> list[str]:
    """Copia os diretorios (source/test/resource/test-resource) dos modulos
    cujo artifactId bate com `pattern` (glob via fnmatch) para uma pasta
    irma do manifesto: <manifest_path sem extensao>.files/<artifactId>/...,
    preservando a mesma subestrutura relativa de directory_structure.
    Retorna os artifactId que bateram com o padrao (lista vazia = nenhum).
    """
    files_root = manifest_path.parent / f"{manifest_path.stem}.files"
    matched: list[str] = []

    def walk(module: Module) -> None:
        artifact_id = module.metadata.artifact_id
        if fnmatch.fnmatch(artifact_id, pattern):
            matched.append(artifact_id)
            module_dir = project.root_path / module.relative_path
            rel_dirs = {
                *module.directory_structure.source_dirs,
                *module.directory_structure.test_dirs,
                *module.directory_structure.resource_dirs,
                *module.directory_structure.test_resource_dirs,
            }
            for rel_dir in rel_dirs:
                src = module_dir / rel_dir
                if src.is_dir():
                    shutil.copytree(
                        src, files_root / artifact_id / rel_dir, dirs_exist_ok=True
                    )
        for sub in module.submodules:
            walk(sub)

    walk(project.root_module)
    return matched
```

- Reaproveita exatamente as mesmas 4 listas de `DirectoryStructure` que `create_project`/`_materialize_directories` já usam — nunca copia `target/`, `.git/`, `pom.xml` (nada disso está em `directory_structure`).
- `fnmatch.fnmatch` (stdlib) para o glob — mesma semântica de shell (`*`, `?`, `[...]`), familiar e suficiente para `shared-*`.
- `dirs_exist_ok=True` no `copytree`: reexportar para o mesmo destino faz merge (não falha se a pasta já existir) — ver risco documentado no requirements.
- Import novo: `import fnmatch`, `import shutil` no topo de `manifest.py`; `Project` já precisa ser importado (hoje só `Module` é usado em `to_manifest`).

## `BuildToolAdapter.create_project` (`src/manager/adapters/base.py`) — parâmetro novo

```python
@abstractmethod
def create_project(
    self,
    manifest: ModuleManifest,
    destination_path: Path,
    *,
    source_root: Path | None = None,
) -> Project:
    """... (docstring existente) ...

    Se source_root for informado, para cada diretorio que seria criado
    vazio, copia de source_root/<artifactId>/<caminho-relativo> quando essa
    pasta existir (preserva codigo-fonte real em vez de so criar a pasta).
    """
```

## `MavenAdapter.create_project`/`_materialize`/`_materialize_directories` (`src/manager/adapters/maven/adapter.py`)

```python
def create_project(
    self, manifest: ModuleManifest, destination_path: Path, *, source_root: Path | None = None
) -> Project:
    validate_manifest_tree(manifest)
    self._validate_maven_manifest(manifest, is_root=True)

    destination_path = destination_path.resolve()
    if destination_path.exists() and any(destination_path.iterdir()):
        raise ValueError(f"'{destination_path}' ja existe e nao esta vazio")
    destination_path.mkdir(parents=True, exist_ok=True)

    self._materialize(manifest, destination_path, None, None, None, source_root)

    return self.infer_structure(destination_path)
```

`_materialize` ganha um parâmetro `source_root: Path | None` a mais, só repassado adiante na recursão (nenhuma outra mudança nessa função) e passado para `_materialize_directories` junto com o `artifact_id` do módulo atual:

```python
self._materialize_directories(
    module_dir, module.directory_structure, source_root, artifact_id
)

for sub in module.submodules:
    self._materialize(
        sub, module_dir / sub.metadata.artifact_id, artifact_id,
        own_group_id, own_version, source_root,
    )
```

`_materialize_directories` (hoje só faz `mkdir` + `register_directory_role` condicional) ganha a lógica de cópia:

```python
def _materialize_directories(
    self, module_dir: Path, structure: DirectoryStructure,
    source_root: Path | None, artifact_id: str,
) -> None:
    module_snapshot = (source_root / artifact_id) if source_root else None
    role_dirs: dict[DirectoryRole, list[str]] = {
        "source": structure.source_dirs,
        "test-source": structure.test_dirs,
        "resource": structure.resource_dirs,
        "test-resource": structure.test_resource_dirs,
    }
    for role, dirs in role_dirs.items():
        for rel_dir in dirs:
            target = module_dir / rel_dir
            snapshot = (module_snapshot / rel_dir) if module_snapshot else None
            if snapshot is not None and snapshot.is_dir():
                shutil.copytree(snapshot, target, dirs_exist_ok=True)
            else:
                target.mkdir(parents=True, exist_ok=True)
            if rel_dir != STANDARD_DIRS[role]:
                self._writer.register_directory_role(
                    module_dir / "pom.xml", rel_dir, role
                )
```

`source_root=None` (default, todo call site/teste existente) → `module_snapshot=None` → `snapshot=None` sempre → cai sempre no `else: mkdir(...)`, idêntico ao comportamento atual. Zero mudança de comportamento para quem não passa o parâmetro novo. Import novo em `adapter.py`: `import shutil`.

## TUI

### `ExportManifestScreen` (`src/manager/screens/export_manifest.py`)

Novo campo `#source-pattern-input` (placeholder `"padrão de módulos p/ código-fonte, ex.: shared-* (opcional)"`), logo abaixo do campo de destino. No `_do_export`, depois de `dump_manifest`:

```python
pattern = self.query_one("#source-pattern-input", Input).value.strip()
if pattern:
    matched = export_source_files(self._project, path, pattern)
    if matched:
        feedback.update(f"[green]Exportado para {path} (código-fonte: {', '.join(matched)})[/green]")
    else:
        feedback.update(f"[yellow]Exportado para {path} (nenhum módulo bateu com '{pattern}')[/yellow]")
else:
    feedback.update(f"[green]Exportado para {path}[/green]")
```

Aviso de "nenhum módulo bateu" não desfaz a exportação da estrutura, que já aconteceu — só informa que o padrão não encontrou nada (erro de digitação do usuário, não falha da operação).

### `CreateProjectScreen` (`src/manager/screens/create_project.py`)

Depois de `manifest = load_manifest(manifest_path)`, antes de chamar `create_project`:

```python
files_dir = manifest_path.parent / f"{manifest_path.stem}.files"
source_root = files_dir if files_dir.is_dir() else None
project = self._adapter.create_project(manifest, destination, source_root=source_root)
```

Sem campo novo nesse formulário — a pasta é detectada automaticamente pela convenção de nome/local estabelecida na exportação.

## Casos de borda tratados

- Padrão vazio: nenhuma pasta `.files` criada (mesmo comportamento da Fase 7).
- Padrão que não bate com nenhum módulo: exportação da estrutura continua normal, só um aviso informativo.
- `.files` existente sem correspondência para um módulo específico do manifesto: esse módulo cai no `mkdir` padrão (comportamento de hoje), sem erro.
- `create_project` chamado sem `source_root` (todo código existente): comportamento idêntico ao pré-Fase-8, testado explicitamente.
- Reexportar para o mesmo `manifest_path` com o mesmo padrão: `copytree(dirs_exist_ok=True)` faz merge por cima, sem falhar.
