import shutil
import subprocess
from pathlib import Path


class GitCloneError(Exception):
    """Falha ao clonar um repositorio remoto (git ausente, destino invalido,
    ou o proprio `git clone` retornou erro)."""


def clone_repository(url: str, destination: Path) -> None:
    """Clona `url` para `destination` via `git clone`.

    Levanta GitCloneError se o git nao estiver instalado, se `destination`
    ja existir e nao estiver vazio, ou se `git clone` retornar codigo de
    saida != 0 (URL invalida, rede, autenticacao) - a mensagem inclui o
    stderr do git quando disponivel, para diagnostico sem abrir um
    terminal. Autenticacao (SSH agent, credential helper, etc.) e
    inteiramente delegada ao git do sistema.
    """
    if shutil.which("git") is None:
        raise GitCloneError("git nao encontrado no PATH")

    destination = destination.expanduser()
    if destination.exists() and any(destination.iterdir()):
        raise GitCloneError(f"'{destination}' ja existe e nao esta vazio")

    result = subprocess.run(
        ["git", "clone", url, str(destination)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitCloneError(result.stderr.strip() or "falha ao clonar o repositorio")
