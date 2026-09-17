# Fase 13 — Clonar Repositório Remoto — Design

## Novo módulo de serviço: `src/manager/services/git.py`

Fica ao lado de `registry.py`/`adapters_registry.py` (serviços de aplicação, fora do modelo de domínio — clonar um repo não é uma operação de `BuildToolAdapter`, é anterior/ortogonal a qualquer build tool).

```python
class GitCloneError(Exception):
    """Falha ao clonar um repositorio remoto (git ausente, destino invalido,
    ou o proprio `git clone` retornou erro)."""


def clone_repository(url: str, destination: Path) -> None:
    """Clona `url` para `destination` via `git clone`.

    Levanta GitCloneError se o git nao estiver instalado (`shutil.which`),
    se `destination` ja existir e nao estiver vazio, ou se `git clone`
    retornar codigo de saida != 0 (URL invalida, rede, autenticacao) - a
    mensagem inclui o stderr do git quando disponivel, para diagnostico
    sem precisar abrir um terminal.
    """
```

`subprocess.run(["git", "clone", url, str(destination)], capture_output=True, text=True)`. Nenhuma dependência Python nova — mesma filosofia já usada para Maven (o projeto nunca invoca `mvn`, só manipula `pom.xml` com `lxml`; aqui, ao contrário, a operação *é* inerentemente git, então invocar o binário `git` é a única opção sensata, não um desvio da filosofia).

## `CloneProjectScreen` (`screens/clone_project.py`)

Espelha `ImportProjectScreen` (mesmo `Screen[bool]`, mesmo padrão de feedback inline), com dois campos (`#url-input`, `#dest-input`) em vez de um. Fluxo:

1. Valida os dois campos não-vazios.
2. `clone_repository(url, destination)` — `GitCloneError` vira mensagem de erro inline, formulário continua aberto (mesmo padrão de erro de `ImportProjectScreen`, nunca fecha sozinho).
3. Clone ok → mesma sequência de `ImportProjectScreen._do_import` a partir do path já existente: `detect_adapter` → `infer_structure` → `ProjectRegistry.add` → feedback de sucesso → `dismiss(True)` num timer curto.
4. Build tool não reconhecida ou falha de inferência após um clone bem-sucedido → mensagem de erro inline (deixa os arquivos clonados no disco, como já é comportamento de `ImportProjectScreen` para um path que falha a inferência), **sem** `dismiss` automático — o usuário decide se fecha (`escape`) ou ajusta algo e tenta de novo (embora tentar de novo aqui não repita o clone, já que os arquivos já estão lá; é só feedback, mesmo com o formulário ainda populado).

## `ProjectsPanel` / `MainScreen`

- Novo binding `("g", "clone_project", "clonar")` em `ProjectsPanel.BINDINGS`.
- `MainScreen`: o closure `_on_dismiss` de `import_project` (recarrega registry, seleciona a última entrada se nada estava selecionado) é extraído para `_on_project_registered` e reaproveitado por `import_project` e pelo novo `clone_project` — idêntico em ambos, só a screen empurrada muda.

## Casos de borda

- Path de destino relativo ou com `~` → `Path(raw_dest).expanduser()`, mesmo tratamento de `ImportProjectScreen`.
- Repositório remoto que é, ele mesmo, um projeto multi-módulo Maven com BOM etc. → nenhuma diferença de `ImportProjectScreen`, já que a partir do clone bem-sucedido o fluxo é idêntico (mesmo `detect_adapter`/`infer_structure`).

## Testes

`clone_repository` é testado isoladamente (`tests/test_git_service.py`) contra um repositório git real criado em `tmp_path` (via `git init` + commit) e clonado por **path local** (não precisa de rede/URL remota de verdade — git trata um path local como uma URL válida para `git clone`). Cobre: clone bem-sucedido, origem inexistente, destino não-vazio, git ausente (mock de `shutil.which`).

## Alternativas descartadas

- Dependência `GitPython` (ou similar) em vez de `subprocess` — descartado: adiciona uma dependência pesada (libgit2/git wrapper) só para rodar exatamente o mesmo `git clone` que o binário já faz sozinho; o projeto já não usa bibliotecas de build tool (nenhum wrapper de Maven), então shell-out direto no `git` é consistente com essa escolha.
- Derivar o path de destino automaticamente do nome do repositório na URL (ex.: `.../foo/bar.git` → `./bar`) — descartado nesta fatia por simplicidade; o usuário informa o destino explicitamente, mesmo padrão de todo outro formulário desta app (nenhum campo tem default "esperto" hoje).
