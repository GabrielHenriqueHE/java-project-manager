from pathlib import Path

from manager.adapters.base import BuildToolAdapter
from manager.adapters.maven.adapter import MavenAdapter

_ADAPTERS: list[BuildToolAdapter] = [MavenAdapter()]


def detect_adapter(root_path: Path) -> BuildToolAdapter | None:
    """Retorna o primeiro adapter conhecido que reconhece root_path, ou None."""
    for adapter in _ADAPTERS:
        if adapter.detect(root_path):
            return adapter
    return None
