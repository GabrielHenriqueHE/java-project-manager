import fnmatch
import shutil
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from manager.models import (
    Dependency,
    DirectoryStructure,
    Module,
    Project,
    ProjectMetadata,
)


class ModuleManifest(BaseModel):
    """Descreve um modulo a ser criado a partir de um manifesto.

    Espelha `Module`, mas sem os campos que so existem depois que o modulo
    ja esta em disco (`relative_path`, `build_file`) e sem `name`/`is_bom`:
    `name` e sempre `metadata.artifact_id` (nunca um valor independente,
    igual ao dominio real) e "e BOM" e sempre derivado de
    packaging+dependencias managed (ver `is_bom_manifest`), nunca um flag
    persistido em lugar nenhum - nao existe tag <isBom> no pom.
    """

    metadata: ProjectMetadata
    dependencies: list[Dependency] = Field(default_factory=list)
    directory_structure: DirectoryStructure = Field(default_factory=DirectoryStructure)
    submodules: list["ModuleManifest"] = Field(default_factory=list)


def to_manifest(module: Module) -> ModuleManifest:
    """Converte um Module ja inferido (uniforme entre build tools) para o
    formato de manifesto - inverso de como create_project materializa um
    ModuleManifest. Descarta os campos que so existem em disco
    (relative_path, build_file) e o `tree` de DirectoryStructure (so serve
    para exibicao da arvore no Painel [5]; create_project nunca le `tree`
    na materializacao).
    """
    directory_structure = module.directory_structure.model_copy(update={"tree": None})
    return ModuleManifest(
        metadata=module.metadata,
        dependencies=module.dependencies,
        directory_structure=directory_structure,
        submodules=[to_manifest(sub) for sub in module.submodules],
    )


def dump_manifest(manifest: ModuleManifest, path: Path) -> None:
    """Serializa o manifesto para YAML em path, sobrescrevendo se existir."""
    data = manifest.model_dump(mode="json", exclude_defaults=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def export_source_files(
    project: Project, manifest_path: Path, pattern: str
) -> list[str]:
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


def load_manifest(path: Path) -> ModuleManifest:
    """Le e valida um arquivo de manifesto YAML."""
    data = yaml.safe_load(path.read_text())
    return ModuleManifest.model_validate(data)


def is_bom_manifest(module: ModuleManifest) -> bool:
    """Mesma regra de `MavenAdapter._build_module`: um modulo e BOM se
    packaging=pom e tiver alguma dependencia managed=True.
    """
    return module.metadata.packaging == "pom" and any(
        dep.managed for dep in module.dependencies
    )


def validate_manifest_tree(root: ModuleManifest) -> None:
    """Validacoes estruturais agnosticas de build tool: nomes de modulo
    (artifactId) presentes e unicos em toda a arvore. Validacoes especificas
    de uma build tool (ex.: regras de heranca de groupId/version do Maven)
    ficam por conta do adapter, chamadas depois desta.
    """
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
