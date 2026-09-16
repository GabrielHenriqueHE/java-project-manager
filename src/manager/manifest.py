from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from manager.models import Dependency, DirectoryStructure, ProjectMetadata


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
