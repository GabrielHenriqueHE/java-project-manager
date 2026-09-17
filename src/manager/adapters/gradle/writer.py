import re
from pathlib import Path
from typing import Callable, Literal

from manager.adapters.gradle.parser import (
    CONFIG_NAMES,
    PLUGIN_ID_RE,
    find_block,
    split_coordinate,
)
from manager.models import Dependency

_JAVA_PLUGIN_IDS = ("java", "java-library", "application")
_PLATFORM_PLUGIN_ID = "java-platform"

_SCOPE_TO_CONFIG: dict[str | None, str] = {
    "compile": "implementation",
    "provided": "compileOnly",
    "runtime": "runtimeOnly",
    "test": "testImplementation",
}

_FULL_DEP_LINE_RE = re.compile(
    r"^[ \t]*(?P<config>" + "|".join(CONFIG_NAMES) + r")"
    r"\s*\(?\s*"
    r"(?P<platform>platform\s*\(\s*)?"
    r"['\"](?P<coord>[^'\"]+)['\"]"
    r"\s*\)?\s*\)?[ \t]*\n?",
    re.MULTILINE,
)

Dialect = Literal["groovy", "kotlin"]


class GradleWriter:
    """Aplica mutacoes pontuais em um build.gradle(.kts)/settings.gradle(.kts)
    existente, via edicao textual cirurgica (regex + contagem de chaves,
    reaproveitando as mesmas gramaticas de `gradle.parser`) - preserva o
    resto do arquivo verbatim, mesmo espirito de "minimizar o diff" do
    `MavenPomWriter`, mas sem uma arvore de sintaxe real por baixo (ver
    phase-15-gradle-fundacao/design.md para os limites do subconjunto
    convencional suportado).
    """

    def dialect(self, path: Path) -> Dialect:
        return "kotlin" if path.name.endswith(".kts") else "groovy"

    def quote(self, dialect: Dialect, value: str) -> str:
        q = '"' if dialect == "kotlin" else "'"
        return f"{q}{value}{q}"

    def plugin_id_literal(self, dialect: Dialect, plugin_id: str) -> str:
        q = '"' if dialect == "kotlin" else "'"
        if dialect == "kotlin":
            return f"id({q}{plugin_id}{q})"
        return f"id {q}{plugin_id}{q}"

    # ---- scalars (group/version) ----

    def set_scalar(self, path: Path, name: str, value: str | None) -> None:
        """Define ou remove uma linha escalar de nivel superior (`group`/
        `version`). Substitui a linha existente no lugar se ja houver uma;
        senao insere logo apos o bloco `plugins {}` (se existir) ou no
        topo do arquivo. `value` falsy remove a linha, sem erro se ja nao
        existir.
        """
        text = path.read_text()
        dialect = self.dialect(path)
        pattern = re.compile(
            rf"^[ \t]*{re.escape(name)}\s*=?\s*['\"][^'\"]*['\"][ \t]*\n?",
            re.MULTILINE,
        )

        if value:
            line = f"{name} = {self.quote(dialect, value)}\n"
            if pattern.search(text):
                text = pattern.sub(line, text, count=1)
            else:
                text = self._insert_after_plugins_or_top(text, line)
        else:
            text = pattern.sub("", text, count=1)

        path.write_text(text)

    def _insert_after_plugins_or_top(self, text: str, line: str) -> str:
        plugins_span = find_block(text, "plugins")
        if plugins_span is not None:
            _, end, _ = plugins_span
            return text[:end] + "\n\n" + line.rstrip("\n") + text[end:]
        return line + "\n" + text if text else line

    # ---- packaging (plugin id swap) ----

    def set_packaging(self, path: Path, packaging: str) -> None:
        """`packaging == "pom"` garante `java-platform` presente e remove
        qualquer plugin da familia `java`/`java-library`/`application`.
        Qualquer outro valor (na pratica sempre `"jar"`) garante que ao
        menos um plugin dessa familia esteja presente (sem trocar um ja
        existente por `java` a forca) e remove `java-platform`. Cria o
        bloco `plugins {}` no topo do arquivo se nao existir nenhum.
        """
        text = path.read_text()
        dialect = self.dialect(path)
        plugins_span = find_block(text, "plugins")

        if plugins_span is None:
            ids_to_add = [_PLATFORM_PLUGIN_ID] if packaging == "pom" else ["java"]
            block = self._render_plugins_block(dialect, ids_to_add)
            path.write_text(block + "\n\n" + text if text else block + "\n")
            return

        start, end, inner = plugins_span
        current_ids = PLUGIN_ID_RE.findall(inner)

        if packaging == "pom":
            to_remove = [pid for pid in current_ids if pid in _JAVA_PLUGIN_IDS]
            to_add = [] if _PLATFORM_PLUGIN_ID in current_ids else [_PLATFORM_PLUGIN_ID]
        else:
            to_remove = [pid for pid in current_ids if pid == _PLATFORM_PLUGIN_ID]
            to_add = (
                [] if any(pid in _JAVA_PLUGIN_IDS for pid in current_ids) else ["java"]
            )

        new_inner = inner
        for plugin_id in to_remove:
            new_inner = self._remove_plugin_line(new_inner, dialect, plugin_id)
        for plugin_id in to_add:
            new_inner = self._append_plugin_line(new_inner, dialect, plugin_id)

        text = text[:start] + text[start:end].replace(inner, new_inner, 1) + text[end:]
        path.write_text(text)

    def _render_plugins_block(self, dialect: Dialect, plugin_ids: list[str]) -> str:
        lines = "\n".join(
            f"    {self.plugin_id_literal(dialect, pid)}" for pid in plugin_ids
        )
        return f"plugins {{\n{lines}\n}}"

    def _append_plugin_line(self, inner: str, dialect: Dialect, plugin_id: str) -> str:
        line = f"    {self.plugin_id_literal(dialect, plugin_id)}\n"
        if inner and not inner.endswith("\n"):
            inner += "\n"
        return inner + line

    def _remove_plugin_line(self, inner: str, dialect: Dialect, plugin_id: str) -> str:
        pattern = re.compile(
            r"^[ \t]*id\s*\(?\s*['\"]" + re.escape(plugin_id) + r"['\"]\s*\)?[ \t]*\n?",
            re.MULTILINE,
        )
        return pattern.sub("", inner, count=1)

    # ---- blocos aninhados: decomposicao recursiva ----

    @staticmethod
    def _replace_block_content(
        text: str, name: str, transform: Callable[[str], str]
    ) -> str | None:
        """Aplica `transform(conteudo) -> novo_conteudo` ao conteudo do
        primeiro bloco `name { ... }` de `text`, preservando cabecalho
        (`name {`) e fechamento (`}`) tal como estao, e todo o resto do
        texto ao redor intocado. Retorna None (sem chamar `transform`) se
        o bloco nao existir - quem chama decide se cria o bloco do zero
        nesse caso.

        Como `transform` recebe so o conteudo interno como uma string
        independente, aninhar chamadas (ex.: tratar `constraints{}` de
        dentro do `transform` de `dependencies{}`) funciona sem nenhuma
        aritmetica de offset absoluto - cada nivel opera na sua propria
        substring e devolve uma nova substring, remontada de fora para
        dentro.
        """
        span = find_block(text, name)
        if span is None:
            return None
        outer_start, outer_end, inner = span
        content_end = outer_end - 1
        content_start = content_end - len(inner)
        header = text[outer_start:content_start]
        closing = text[content_end:outer_end]
        new_inner = transform(inner)
        return text[:outer_start] + header + new_inner + closing + text[outer_end:]

    # ---- dependencias (upsert) ----

    def _render_dep_line(
        self, dialect: Dialect, config: str, dependency: Dependency, indent: str
    ) -> str:
        coord = f"{dependency.group_id}:{dependency.artifact_id}"
        if dependency.version:
            coord += f":{dependency.version}"
        if dialect == "kotlin":
            return f'{indent}{config}("{coord}")\n'
        return f"{indent}{config} '{coord}'\n"

    def _upsert_dep_line_in_text(
        self,
        text: str,
        dialect: Dialect,
        dependency: Dependency,
        *,
        config: str,
        indent: str,
        exclude_span: tuple[int, int] | None = None,
    ) -> str:
        """Substitui, dentro de `text`, a linha de dependencia existente
        para (group_id, artifact_id) por uma nova renderizada com
        `config`/`indent` atuais; anexa uma linha nova ao final de `text`
        se nao encontrar nenhuma. `exclude_span` (offsets absolutos
        dentro de `text`) pula matches que caiam dentro dele - usado para
        nao confundir uma linha gerenciada, dentro de `constraints{}`,
        com uma linha direta durante a busca.
        """
        new_line = self._render_dep_line(dialect, config, dependency, indent)
        for match in _FULL_DEP_LINE_RE.finditer(text):
            if exclude_span and exclude_span[0] <= match.start() < exclude_span[1]:
                continue
            parsed = split_coordinate(match.group("coord"))
            if parsed is None:
                continue
            group_id, artifact_id, _ = parsed
            if (
                group_id == dependency.group_id
                and artifact_id == dependency.artifact_id
            ):
                return text[: match.start()] + new_line + text[match.end() :]

        if text and not text.endswith("\n"):
            text += "\n"
        return text + new_line

    def _upsert_direct_line(
        self, inner: str, dialect: Dialect, dependency: Dependency
    ) -> str:
        config = _SCOPE_TO_CONFIG.get(dependency.scope, "implementation")
        constraints_span = find_block(inner, "constraints")
        exclude = (
            (constraints_span[0], constraints_span[1]) if constraints_span else None
        )
        return self._upsert_dep_line_in_text(
            inner,
            dialect,
            dependency,
            config=config,
            indent="    ",
            exclude_span=exclude,
        )

    def _upsert_managed_line(
        self, inner: str, dialect: Dialect, dependency: Dependency
    ) -> str:
        def transform(constraints_inner: str) -> str:
            return self._upsert_dep_line_in_text(
                constraints_inner, dialect, dependency, config="api", indent="        "
            )

        new_inner = self._replace_block_content(inner, "constraints", transform)
        if new_inner is not None:
            return new_inner

        line = self._render_dep_line(dialect, "api", dependency, "        ")
        block = f"    constraints {{\n{line}    }}\n"
        if inner and not inner.endswith("\n"):
            inner += "\n"
        return inner + block

    def upsert_dependency(self, path: Path, dependency: Dependency) -> None:
        """Adiciona ou atualiza (upsert por group_id:artifact_id) uma
        dependencia. Gerenciada (`dependency.managed`) sempre vai para
        dentro de `constraints{}` (criado se nao existir), config sempre
        `api` (convencao das duas fixtures); direta vai na porcao de
        `dependencies{}` fora de `constraints{}`, config escolhido a
        partir de `dependency.scope` (aproximado - Gradle tem mais
        granularidade que `DependencyScope`, mesma limitacao documentada
        no lado de leitura em `CONFIG_TO_SCOPE`).
        """
        text = path.read_text()
        dialect = self.dialect(path)

        def transform(inner: str) -> str:
            if dependency.managed:
                return self._upsert_managed_line(inner, dialect, dependency)
            return self._upsert_direct_line(inner, dialect, dependency)

        new_text = self._replace_block_content(text, "dependencies", transform)
        if new_text is None:
            new_inner = transform("")
            block = f"dependencies {{\n{new_inner}}}\n"
            new_text = (text.rstrip("\n") + "\n\n" + block) if text.strip() else block

        path.write_text(new_text)

    # ---- update_metadata orchestration ----

    def update_metadata(
        self,
        path: Path,
        *,
        group_id: str | None,
        version: str | None,
        packaging: str | None,
    ) -> None:
        """Atualiza group/version (literal, sem heranca - o parser nunca
        le `allprojects{}`, entao nao ha "herdar do pai" a considerar
        aqui) e, se `packaging` for informado, troca o plugin conforme
        `set_packaging`.

        `packaging=None` significa "sem mudanca de packaging" e deixa os
        plugins intocados de proposito: ao contrario do Maven (onde
        `<packaging>` e sempre reescrito, mas isso e barato/idempotente
        em XML), aqui packaging="pom" e ambiguo entre "aggregator puro,
        sem nenhum plugin" e "BOM via java-platform" - reescrever
        incondicionalmente a cada chamada de update_metadata bolaria um
        `java-platform` do nada num aggregator puro so por causa de uma
        troca de version, por exemplo. `GradleAdapter.update_metadata`
        so passa um valor aqui quando o packaging pedido realmente
        difere do atual do modulo.
        """
        if packaging is not None:
            self.set_packaging(path, packaging)
        self.set_scalar(path, "group", group_id)
        self.set_scalar(path, "version", version)
