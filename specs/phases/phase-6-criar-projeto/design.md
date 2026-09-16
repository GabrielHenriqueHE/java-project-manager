# Fase 6 — Criar Projeto a Partir de Manifesto — Design

## Novo módulo `src/manager/manifest.py` (agnóstico de build tool)

```python
from pathlib import Path
import yaml
from pydantic import BaseModel, Field
from manager.models import Dependency, DirectoryStructure, ProjectMetadata


class ModuleManifest(BaseModel):
    """Descreve um modulo a ser criado. Espelha `Module`, mas sem os campos
    que so existem depois que o modulo ja esta em disco (`relative_path`,
    `build_file`) e sem `name`/`is_bom` (ver justificativa abaixo)."""

    metadata: ProjectMetadata
    dependencies: list[Dependency] = Field(default_factory=list)
    directory_structure: DirectoryStructure = Field(default_factory=DirectoryStructure)
    submodules: list["ModuleManifest"] = Field(default_factory=list)


def load_manifest(path: Path) -> ModuleManifest:
    data = yaml.safe_load(path.read_text())
    return ModuleManifest.model_validate(data)


def is_bom_manifest(module: ModuleManifest) -> bool:
    """Mesma regra de `MavenAdapter._build_module`: BOM e derivado
    (packaging=pom + alguma dependencia managed=True), nunca um flag
    explicito no manifesto — evita o manifesto declarar `is_bom: true` e
    dependencyManagement vazio, uma contradicao que o dominio real nunca
    permite (`Module.is_bom` tambem e sempre derivado, nunca persistido)."""
    return module.metadata.packaging == "pom" and any(
        dep.managed for dep in module.dependencies
    )


def validate_manifest_tree(root: ModuleManifest) -> None:
    """Validacoes estruturais agnosticas de build tool (nomes duplicados).
    Validacoes especificas de Maven (groupId/version obrigatorios na raiz,
    packaging=pom para quem tem submodulos/e BOM, version obrigatoria em
    dependencia managed, no maximo um BOM na arvore) ficam em
    MavenAdapter._validate_manifest, chamada depois desta."""
    seen: set[str] = set()

    def walk(module: ModuleManifest) -> None:
        artifact_id = module.metadata.artifact_id
        if not artifact_id:
            raise ValueError("Todo modulo do manifesto precisa de metadata.artifact_id")
        if artifact_id in seen:
            raise ValueError(f"Nome de modulo duplicado no manifesto: '{artifact_id}'")
        seen.add(artifact_id)
        for sub in module.submodules:
            walk(sub)

    walk(root)
```

**Por que sem `name` nem `is_bom` no schema:** no modelo de domínio real, `Module.name` é sempre literalmente `parsed.metadata.artifact_id` (`MavenAdapter._build_module`) e `Module.is_bom` é sempre derivado (`packaging == "pom" and bool(managed_dependencies)`), nunca persistido em nenhum lugar — não existe tag `<isBom>` no pom. Dar ao manifesto um `name`/`is_bom` próprios abriria espaço para contradição (`name` diferente de `metadata.artifact_id`, ou `is_bom: true` sem nenhuma dependência managed) que o domínio real nunca permite. O manifesto usa exatamente as mesmas regras derivadas.

**Por que `directory_structure` tem default e isso é aceito:** `DirectoryStructure` (reaproveitado tal qual do domínio) já teria default `source_dirs=["src/main/java"]` etc. se omitido no YAML — mesmo comportamento que `Module()` já tem hoje quando construído sem `directory_structure` explícito (ver `MainScreen._quick_add_module`, que também deixa o default cair em `add_module`). Não é uma inconsistência nova desta fatia; um módulo BOM/agregador puro que não deve ganhar `src/main/java` precisa declarar `directory_structure` com as 4 listas vazias explicitamente no manifesto.

## `pyproject.toml`

Adiciona `pyyaml` às dependências do projeto (não é dev-only: `load_manifest` é código de produção).

## `MavenPomWriter.create_pom` — duas extensões (`src/manager/adapters/maven/writer.py`)

```python
def create_pom(
    self,
    pom_path: Path,
    *,
    parent_group_id: str | None = None,
    parent_artifact_id: str | None = None,
    parent_version: str | None = None,
    artifact_id: str,
    group_id: str | None = None,
    version: str | None = None,
    packaging: str = "jar",
    name: str | None = None,
    description: str | None = None,
    dependencies: list[Dependency] | None = None,
    submodule_names: list[str] | None = None,
) -> None:
```

1. **Parent opcional**: os 3 `parent_*` passam de obrigatórios para `None` por padrão. O bloco `<parent>` só é escrito se os 3 estiverem presentes (`if parent_group_id and parent_artifact_id and parent_version:`). Todo call site existente (`add_module`) já passa os 3 sempre — comportamento idêntico, zero mudança nos testes existentes.
2. **`submodule_names`**: se não-vazio, escreve `<modules><module>x</module>...</modules>` logo depois do bloco `<dependencies>` (mesma posição de `POM_ELEMENT_ORDER`: `..., "dependencies", "modules", "build"`), usando o mesmo helper `child()` já usado para todos os outros elementos — sem isso, um pom recém-criado com submódulos não teria onde `add_module_entry`/`create_project` inserir `<module>` depois (esse método hoje exige `<modules>` já existente e retorna `False` caso contrário).

Nenhuma mudança nos testes de `add_module`/`test_maven_pom_writer*` existentes: os dois parâmetros novos são estritamente aditivos com defaults que reproduzem o comportamento atual.

## `directory.py` — `_STANDARD_DIRS` vira `STANDARD_DIRS` (público)

Simples rename (sem mudança de valor) para que `MavenAdapter.create_project` possa reaproveitar o mesmo mapeamento role→caminho convencional, em vez de duplicá-lo — mesmo raciocínio já aplicado a `build_helper.py` na fatia anterior.

## `BuildToolAdapter.create_project` (`src/manager/adapters/base.py`)

```python
@abstractmethod
def create_project(self, manifest: ModuleManifest, destination_path: Path) -> Project:
    """Materializa um projeto novo em destination_path a partir de manifest.

    Valida a arvore inteira antes de qualquer escrita. destination_path
    precisa nao existir ou estar vazio. Retorna infer_structure(destination_path).
    """
```

## `MavenAdapter.create_project` (`src/manager/adapters/maven/adapter.py`)

```python
def create_project(self, manifest: ModuleManifest, destination_path: Path) -> Project:
    validate_manifest_tree(manifest)         # generico (nomes duplicados)
    self._validate_maven_manifest(manifest)  # especifico de Maven, ve abaixo

    destination_path = destination_path.resolve()
    if destination_path.exists() and any(destination_path.iterdir()):
        raise ValueError(f"'{destination_path}' ja existe e nao esta vazio")
    destination_path.mkdir(parents=True, exist_ok=True)

    self._materialize(manifest, destination_path, parent_artifact_id=None,
                       effective_group_id=None, effective_version=None)

    return self.infer_structure(destination_path)
```

### `_validate_maven_manifest` (validações específicas de Maven, antes de qualquer escrita)

Percorre a árvore recursivamente e levanta `ValueError` (mensagens no mesmo estilo das já existentes em `add_module`/`update_metadata`/`update_dependency`) se:
- **Raiz sem `group_id`/`version`**: raiz não tem `<parent>` de quem herdar — mesma regra de `update_metadata` ("Modulo raiz nao tem parent para herdar: groupId e version sao obrigatorios").
- **Módulo com submódulos ou que é BOM (`is_bom_manifest`) com `packaging != "pom"`** — mesma regra de `update_metadata` para módulo com submódulos/BOM.
- **Dependência `managed=True` sem `version`** — mesma regra de `update_dependency`.
- **Mais de um módulo com `is_bom_manifest(module) is True` na árvore inteira** — regra nova desta fatia: o domínio assume um único BOM por projeto (`_find_bom_module` retorna o primeiro encontrado); um manifesto com dois módulos BOM seria ambíguo.

### `_materialize` (recursivo, escreve em disco)

Resolve a herança efetiva de `group_id`/`version` **durante a caminhada da árvore** (não comparando contra o valor bruto do manifesto do pai, que pode ele mesmo estar herdando) — ponto sutil: ao contrário de um `Module` já inferido (onde `metadata.group_id` é sempre o valor **efetivo** resolvido pelo parser), no manifesto um `ModuleManifest.metadata.group_id` pode ser `None` em qualquer nível para dizer "herdar". Por isso a recursão carrega os valores efetivos já resolvidos do pai como parâmetros, em vez de reler `parent.metadata.group_id` bruto:

```python
def _materialize(
    self,
    module: ModuleManifest,
    module_dir: Path,
    parent_artifact_id: str | None,
    effective_group_id: str | None,
    effective_version: str | None,
) -> tuple[str, str]:
    artifact_id = module.metadata.artifact_id
    submodule_names = [sub.metadata.artifact_id for sub in module.submodules] or None

    if parent_artifact_id is None:
        # raiz: ja validado que group_id/version estao presentes
        own_group_id = module.metadata.group_id
        own_version = module.metadata.version
        self._writer.create_pom(
            module_dir / "pom.xml",
            artifact_id=artifact_id,
            group_id=own_group_id,
            version=own_version,
            packaging=module.metadata.packaging,
            name=module.metadata.name,
            description=module.metadata.description,
            dependencies=module.dependencies,
            submodule_names=submodule_names,
        )
    else:
        own_group_id = module.metadata.group_id or effective_group_id
        own_version = module.metadata.version or effective_version
        write_group_id = (
            module.metadata.group_id
            if module.metadata.group_id and module.metadata.group_id != effective_group_id
            else None
        )
        write_version = (
            module.metadata.version
            if module.metadata.version and module.metadata.version != effective_version
            else None
        )
        self._writer.create_pom(
            module_dir / "pom.xml",
            parent_group_id=effective_group_id,
            parent_artifact_id=parent_artifact_id,
            parent_version=effective_version,
            artifact_id=artifact_id,
            group_id=write_group_id,
            version=write_version,
            packaging=module.metadata.packaging,
            name=module.metadata.name,
            description=module.metadata.description,
            dependencies=module.dependencies,
            submodule_names=submodule_names,
        )

    self._materialize_directories(module_dir, module.directory_structure)

    for sub in module.submodules:
        self._materialize(
            sub, module_dir / sub.metadata.artifact_id,
            artifact_id, own_group_id, own_version,
        )

    return own_group_id, own_version


def _materialize_directories(self, module_dir: Path, structure: DirectoryStructure) -> None:
    role_dirs: dict[DirectoryRole, list[str]] = {
        "source": structure.source_dirs,
        "test-source": structure.test_dirs,
        "resource": structure.resource_dirs,
        "test-resource": structure.test_resource_dirs,
    }
    for role, dirs in role_dirs.items():
        for rel_dir in dirs:
            (module_dir / rel_dir).mkdir(parents=True, exist_ok=True)
            if rel_dir != STANDARD_DIRS[role]:
                self._writer.register_directory_role(
                    module_dir / "pom.xml", rel_dir, role
                )
```

`write_group_id`/`write_version` seguem exatamente a mesma expressão já usada em `add_module`, só trocando `parent.metadata.group_id` (valor bruto de um `Module` já resolvido) por `effective_group_id` (valor já resolvido carregado pela recursão). `_materialize_directories` reaproveita a mesma lógica dupla já usada em `register_directory_role`/`add_directory`: qualquer diretório que não seja o caminho convencional (`STANDARD_DIRS[role]`) precisa, além do `mkdir`, de uma `<execution>` do `build-helper-maven-plugin` — a mesma chamada de escrita já usada em `MavenAdapter.register_directory_role`, só que aqui direto no pom recém-criado (que já existe em disco nesse ponto da recursão, então `register_directory_role` do writer — que só mexe em XML, não valida disco — funciona sem problema).

## TUI

- `CreateProjectScreen` (`src/manager/screens/create_project.py`, novo, `Screen[bool]`, mesmo padrão de `ImportProjectScreen`): dois campos — `#manifest-input` (caminho do arquivo de manifesto) e `#destination-input` (diretório de destino). Confirmar: `load_manifest(path)` (captura `FileNotFoundError`/`yaml.YAMLError`/`pydantic.ValidationError` → feedback no próprio form, sem chamar o adapter) e, se ok, `self.screen.create_project(manifest, destination_path)`; dismiss(True) em sucesso (mesmo padrão de `_finish` em `ImportProjectScreen`).
- `ProjectsPanel` ganha o binding `("c", "create_project", "criar")`; `action_create_project` chama `self.screen.create_project()` (abre a tela, sem argumentos — paralelo a `action_import_project`).
- `MainScreen.create_project()`: abre `CreateProjectScreen`; no callback de sucesso, registra o novo projeto no `ProjectRegistry` (mesmo `self._registry.add(path, adapter.build_tool)` de `ImportProjectScreen._do_import`) e seleciona o projeto (`self.select_project(...)` ou `set_project` direto, já que o `Project` retornado por `create_project` já é o inferido).
- Só `MavenAdapter` é instanciado diretamente nesta fatia (sem `detect_adapter`, que depende de um `pom.xml` já existir) — condizente com o "fora de escopo" de suporte a outras build tools já registrado no requirements.

## Testes

- `tests/test_manifest.py`: `load_manifest` parse YAML válido; `validate_manifest_tree` rejeita nome duplicado / `artifact_id` ausente; `is_bom_manifest` verdadeiro só com packaging pom + dependência managed.
- `tests/test_maven_pom_writer_create_pom.py` (ou extensão de um arquivo de writer existente, a decidir na implementação): `create_pom` sem nenhum `parent_*` omite `<parent>`; `submodule_names` escreve `<modules>` na posição certa; chamada com os 3 `parent_*` continua idêntica ao comportamento anterior.
- `tests/test_maven_adapter_create_project.py`: projeto de um módulo só; projeto multi-módulo com herança de groupId/version; projeto com BOM (dependencyManagement no pom do módulo BOM, dependência direta resolvida noutro módulo); diretório customizado no manifesto materializa `mkdir` + `register_directory_role`; diretório convencional só faz `mkdir`; erros de validação (raiz sem groupId/version, dois módulos BOM, dependência managed sem version, nome duplicado) não escrevem nada em disco; `destination_path` já existente e não vazio falha sem escrever; retorno de `create_project` bate com uma chamada equivalente a `infer_structure` no resultado.
- `tests/test_main_screen.py`: fluxo de criação via `CreateProjectScreen` materializa o projeto e o seleciona; manifesto inválido mantém o formulário aberto com feedback; cancelar não cria nada.
