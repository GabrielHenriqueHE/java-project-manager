import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from manager.models import BuildTool

DEFAULT_REGISTRY_PATH = (
    Path.home() / ".config" / "java-project-manager" / "registry.json"
)


class RegistryEntry(BaseModel):
    path: Path
    build_tool: BuildTool
    last_opened: datetime | None = None


class ProjectRegistry:
    """Lista de projetos conhecidos pela aplicacao.

    Guardada fora do modelo de dominio (nao e dado de um projeto Java, e
    dado da propria ferramenta) em um JSON no diretorio de config do usuario.
    """

    def __init__(self, registry_path: Path | None = None):
        self._registry_path = registry_path or DEFAULT_REGISTRY_PATH

    def load(self) -> list[RegistryEntry]:
        if not self._registry_path.is_file():
            return []
        data = json.loads(self._registry_path.read_text())
        return [RegistryEntry.model_validate(item) for item in data]

    def save(self, entries: list[RegistryEntry]) -> None:
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [entry.model_dump(mode="json") for entry in entries]
        self._registry_path.write_text(json.dumps(payload, indent=2))

    def add(self, path: Path, build_tool: BuildTool) -> RegistryEntry:
        path = path.resolve()
        entries = [entry for entry in self.load() if entry.path != path]
        entry = RegistryEntry(
            path=path, build_tool=build_tool, last_opened=datetime.now(timezone.utc)
        )
        entries.append(entry)
        self.save(entries)
        return entry

    def remove(self, path: Path) -> None:
        path = path.resolve()
        entries = [entry for entry in self.load() if entry.path != path]
        self.save(entries)
