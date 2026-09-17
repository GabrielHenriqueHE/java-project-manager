import re
from pathlib import Path
from typing import Literal

from manager.adapters.gradle.parser import PLUGIN_ID_RE, find_block

_JAVA_PLUGIN_IDS = ("java", "java-library", "application")
_PLATFORM_PLUGIN_ID = "java-platform"

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
