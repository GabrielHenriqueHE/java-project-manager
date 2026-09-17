import re
from dataclasses import dataclass, field
from pathlib import Path

from manager.models import Dependency

BUILD_FILE_NAMES = ("build.gradle.kts", "build.gradle")
SETTINGS_FILE_NAMES = ("settings.gradle.kts", "settings.gradle")

_JAVA_PLUGIN_IDS = frozenset({"java", "java-library", "application"})
_PLATFORM_PLUGIN_ID = "java-platform"

CONFIG_NAMES = (
    "implementation",
    "api",
    "compileOnly",
    "runtimeOnly",
    "testImplementation",
    "testRuntimeOnly",
    "testCompileOnly",
    "annotationProcessor",
    "testAnnotationProcessor",
)

CONFIG_TO_SCOPE: dict[str, str | None] = {
    "implementation": "compile",
    "api": "compile",
    "compileOnly": "provided",
    "runtimeOnly": "runtime",
    "testImplementation": "test",
    "testRuntimeOnly": "test",
    "testCompileOnly": "test",
    "annotationProcessor": "provided",
    "testAnnotationProcessor": "test",
}

PLUGIN_ID_RE = re.compile(r"id\s*\(?\s*['\"]([\w.\-]+)['\"]\s*\)?")
DEP_LINE_RE = re.compile(
    r"^[ \t]*(?P<config>" + "|".join(CONFIG_NAMES) + r")"
    r"\s*\(?\s*"
    r"(?P<platform>platform\s*\(\s*)?"
    r"['\"](?P<coord>[^'\"]+)['\"]",
    re.MULTILINE,
)
ROOT_NAME_RE = re.compile(r"rootProject\.name\s*=\s*['\"]([^'\"]+)['\"]")
INCLUDE_RE = re.compile(r"\binclude\s*\(?\s*((?:['\"][^'\"]+['\"]\s*,?\s*)+)\)?")
QUOTED_RE = re.compile(r"['\"]([^'\"]+)['\"]")


@dataclass
class ParsedGradleBuild:
    build_file_path: Path
    group_id: str | None
    version: str | None
    plugin_ids: list[str] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
    managed_dependencies: list[Dependency] = field(default_factory=list)

    @property
    def is_platform(self) -> bool:
        return _PLATFORM_PLUGIN_ID in self.plugin_ids

    @property
    def has_java_plugin(self) -> bool:
        return any(plugin in _JAVA_PLUGIN_IDS for plugin in self.plugin_ids)


def find_build_file(module_dir: Path) -> Path | None:
    for name in BUILD_FILE_NAMES:
        candidate = module_dir / name
        if candidate.is_file():
            return candidate
    return None


def find_settings_file(root_path: Path) -> Path | None:
    for name in SETTINGS_FILE_NAMES:
        candidate = root_path / name
        if candidate.is_file():
            return candidate
    return None


def parse_build_file(path: Path) -> ParsedGradleBuild:
    """Le um build.gradle/build.gradle.kts isolado (Groovy ou Kotlin DSL) e
    extrai plugins, group/version e dependencias, via varredura por regex
    de um subconjunto convencional da linguagem (sem interpretar Groovy/
    Kotlin de verdade - ver phase-15-gradle-fundacao/design.md para o
    exato subconjunto suportado e as limitacoes conhecidas).
    """
    text = path.read_text()

    plugins_span = find_block(text, "plugins")
    plugin_ids = PLUGIN_ID_RE.findall(plugins_span[2]) if plugins_span else []
    text_without_plugins = (
        text[: plugins_span[0]] + text[plugins_span[1] :] if plugins_span else text
    )

    group_id = _extract_scalar(text_without_plugins, "group")
    version = _extract_scalar(text_without_plugins, "version")

    deps_block = _extract_block(text, "dependencies")
    dependencies, managed_dependencies = (
        _parse_dependencies_block(deps_block) if deps_block is not None else ([], [])
    )

    return ParsedGradleBuild(
        build_file_path=path,
        group_id=group_id,
        version=version,
        plugin_ids=plugin_ids,
        dependencies=dependencies,
        managed_dependencies=managed_dependencies,
    )


@dataclass
class ParsedSettings:
    root_name: str | None
    modules: list[tuple[str, str]] = field(default_factory=list)
    """Lista de (nome, caminho_relativo) - um por projeto incluido via
    `include`. `nome` e o ultimo segmento do path Gradle (separado por
    ':'), usado como artifactId/nome do modulo; `caminho_relativo` e esse
    mesmo path convertido para separador de diretorio ('/'), usado para
    localizar o modulo em disco. Projetos incluidos sao sempre modelados
    como filhos diretos do modulo raiz nesta fase, mesmo quando o path
    Gradle tem mais de um segmento (ex.: ':modulos:core') - ver design.md.
    """


def parse_settings_file(path: Path) -> ParsedSettings:
    text = path.read_text()
    root_match = ROOT_NAME_RE.search(text)
    root_name = root_match.group(1) if root_match else None

    modules: list[tuple[str, str]] = []
    for include_match in INCLUDE_RE.finditer(text):
        for quoted in QUOTED_RE.finditer(include_match.group(1)):
            raw = quoted.group(1)
            colon_path = raw[1:] if raw.startswith(":") else raw
            if not colon_path:
                continue
            relative_path = colon_path.replace(":", "/")
            name = colon_path.rsplit(":", 1)[-1]
            modules.append((name, relative_path))

    return ParsedSettings(root_name=root_name, modules=modules)


def _parse_dependencies_block(
    deps_block: str,
) -> tuple[list[Dependency], list[Dependency]]:
    managed: list[Dependency] = []
    direct: list[Dependency] = []

    remainder = deps_block
    constraints_span = find_block(deps_block, "constraints")
    if constraints_span is not None:
        outer_start, outer_end, inner = constraints_span
        for match in DEP_LINE_RE.finditer(inner):
            dep = _dependency_from_match(match, managed=True)
            if dep is not None:
                managed.append(dep)
        remainder = deps_block[:outer_start] + deps_block[outer_end:]

    for match in DEP_LINE_RE.finditer(remainder):
        is_platform = match.group("platform") is not None
        dep = _dependency_from_match(match, managed=is_platform)
        if dep is None:
            continue
        (managed if dep.managed else direct).append(dep)

    return direct, managed


def _dependency_from_match(match: re.Match[str], *, managed: bool) -> Dependency | None:
    parsed = split_coordinate(match.group("coord"))
    if parsed is None:
        return None
    group_id, artifact_id, version = parsed
    config = match.group("config")
    return Dependency(
        group_id=group_id,
        artifact_id=artifact_id,
        version=version,
        scope=None if managed else CONFIG_TO_SCOPE.get(config),
        managed=managed,
    )


def split_coordinate(raw: str) -> tuple[str, str, str | None] | None:
    """Divide uma notacao 'group:artifact[:version]' de dependencia Gradle.

    Retorna None se `raw` for uma referencia de projeto Gradle (comeca com
    ':', ex. ':core' de `project(':core')`) em vez de uma coordenada
    externa - referencias de projeto nao tem group/artifact/version
    literais para modelar como Dependency (ver design.md).
    """
    if raw.startswith(":"):
        return None
    parts = raw.split(":")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return None
    version = parts[2] if len(parts) > 2 and parts[2] else None
    return parts[0], parts[1], version


def _extract_scalar(text: str, name: str) -> str | None:
    match = re.search(rf"^[ \t]*{name}\s*=?\s*['\"]([^'\"]+)['\"]", text, re.MULTILINE)
    return match.group(1) if match else None


def _extract_block(text: str, name: str) -> str | None:
    found = find_block(text, name)
    return found[2] if found is not None else None


def find_block(text: str, name: str) -> tuple[int, int, str] | None:
    """Localiza o primeiro bloco `name { ... }`, com contagem de chaves
    para lidar com blocos aninhados corretamente. Retorna
    (inicio_externo, fim_externo, conteudo_interno); fim_externo e o
    indice logo apos o '}' de fechamento, para permitir recortar o bloco
    inteiro (cabecalho incluso) do texto original.
    """
    match = re.search(rf"\b{name}\s*\{{", text)
    if match is None:
        return None
    depth = 1
    i = match.end()
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    if depth != 0:
        return None
    return match.start(), i, text[match.end() : i - 1]
