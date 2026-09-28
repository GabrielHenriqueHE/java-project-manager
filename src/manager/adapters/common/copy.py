import shutil
from pathlib import Path

_BUILD_OUTPUT_IGNORE = shutil.ignore_patterns(
    "target", "build", "bin", ".gradle", "out", ".git", ".idea"
)


def copy_module_tree(source_dir: Path, dest_dir: Path) -> None:
    """Copia a arvore de arquivos de um modulo inteira (codigo-fonte,
    resources, arquivo de build, qualquer outro arquivo), ignorando
    saida de build/VCS/IDE conhecidos. Usado por duplicate_module
    (Gradle e Maven) para usar um modulo existente como template literal.
    """
    shutil.copytree(source_dir, dest_dir, ignore=_BUILD_OUTPUT_IGNORE)
