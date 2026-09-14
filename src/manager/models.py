from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

BuildTool = Literal["maven", "gradle"]
DependencyScope = Literal["compile", "provided", "runtime", "test", "system", "import"]
DirectoryRole = Literal["source", "test-source", "resource", "test-resource", "other"]


class Dependency(BaseModel):
    group_id: str
    artifact_id: str
    version: str | None = None
    scope: DependencyScope | None = None
    type: str | None = None
    classifier: str | None = None
    managed: bool = False


class ProjectMetadata(BaseModel):
    group_id: str | None = None
    artifact_id: str
    version: str | None = None
    name: str | None = None
    description: str | None = None
    packaging: str = "jar"
    properties: dict[str, str] = Field(default_factory=dict)


class DirectoryNode(BaseModel):
    name: str
    role: DirectoryRole = "other"
    children: list["DirectoryNode"] = Field(default_factory=list)


class DirectoryStructure(BaseModel):
    convention: Literal["maven-standard", "custom"] = "maven-standard"
    source_dirs: list[str] = Field(default_factory=lambda: ["src/main/java"])
    test_dirs: list[str] = Field(default_factory=lambda: ["src/test/java"])
    resource_dirs: list[str] = Field(default_factory=lambda: ["src/main/resources"])
    test_resource_dirs: list[str] = Field(
        default_factory=lambda: ["src/test/resources"]
    )
    tree: DirectoryNode | None = None


class BuildFile(BaseModel):
    path: Path
    kind: Literal["build-file"] = "build-file"


class Module(BaseModel):
    name: str
    relative_path: Path
    metadata: ProjectMetadata
    dependencies: list[Dependency] = Field(default_factory=list)
    directory_structure: DirectoryStructure = Field(default_factory=DirectoryStructure)
    build_file: BuildFile
    submodules: list["Module"] = Field(default_factory=list)
    is_bom: bool = False


class Project(BaseModel):
    name: str
    build_tool: BuildTool
    root_path: Path
    root_module: Module
    managed_dependencies: list[Dependency] = Field(default_factory=list)
