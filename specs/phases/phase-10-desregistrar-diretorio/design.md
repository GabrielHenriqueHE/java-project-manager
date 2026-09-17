# Fase 10 — Desregistrar Diretório do Build — Design

## `MavenPomWriter.unregister_directory_role` (`writer.py`)

Inverso simétrico de `register_directory_role`: recalcula o mesmo `execution_id = f"add-{role}-" + relative_path.replace("/", "-")` usado na escrita, localiza a `<execution>` pelo id dentro do plugin `build-helper-maven-plugin` (via `_find_plugin_element`/`_find_execution_element`, já existentes) e remove com `remove_element_preserving_whitespace`. Limpa em cascata `<executions>` → `<plugin>` → `<plugins>` → `<build>` sempre que cada um fica vazio, no mesmo padrão de `remove_managed_dependency` (que já limpa `<dependencies>` → `<dependencyManagement>`). Retorna `False` sem escrever se `<build>`, `<plugins>`, o plugin ou a execution não existirem — mesma convenção de retorno booleano dos outros métodos de remoção do writer.

## `MavenAdapter.unregister_directory_role` (`adapter.py`)

Mesma validação de entrada de `register_directory_role` (módulo existe, role é um dos 4 registráveis), sem a checagem de existência em disco (aqui não temos disco algum a inspecionar — a operação é só na entrada do build). Chama o writer; se retornar `False`, levanta `ValueError` ("diretório não estava registrado no build"). Retorna `infer_structure(project.root_path)`.

## Interface (`base.py`)

Novo `@abstractmethod unregister_directory_role(project, module_name, relative_path, role) -> Project`, assinatura idêntica a `register_directory_role`.

## TUI

- `BuildSourceFormScreen` (`build_source_form.py`) ganha `title`/`confirm_label` opcionais (defaults iguais aos atuais) em vez de um modal novo duplicado — o formulário (caminho + role, mesma validação) é idêntico para registrar e desregistrar, só muda o rótulo e o que acontece com o resultado.
- `StructurePanel`: novo binding `u` → `action_unregister_build_source` → `self.screen.unregister_build_source(active_module)`.
- `MainScreen.unregister_build_source(module)`: abre `BuildSourceFormScreen(title="Desregistrar diretorio do build", confirm_label="Desregistrar")`, chama `self._adapter.unregister_directory_role(...)`, notifica e atualiza o projeto — mesmo formato de `register_build_source`.
- Rodapé/README: novo atalho `u` documentado ao lado de `b`.

## Casos de borda

- Desregistrar um diretório que também é convenção padrão de outro role (não ocorre na prática — `execution_id` é único por `(role, relative_path)`, e convenção padrão nunca é escrita via build-helper).
- Desregistrar não apaga o diretório do disco nem o remove de `source_dirs`/etc. na *mesma* chamada — isso só acontece na `infer_structure` seguinte (mesmo padrão de toda mutação no projeto: adapter escreve, depois re-infere).

## Alternativas descartadas

- Modal novo dedicado a desregistrar, duplicando `BuildSourceFormScreen` — descartado por ser exatamente os mesmos dois campos e a mesma validação; parametrizar título/rótulo é a reutilização mais simples.
- Inferir a `role` automaticamente a partir de `source_dirs`/etc. no lugar de pedir no formulário — descartado porque o mesmo `relative_path` poderia, em teoria, aparecer registrado sob roles diferentes em módulos diferentes, e o formulário livre (sem pré-seleção de item da árvore) já pede os dois campos hoje para registrar; pedir os dois de novo para desregistrar mantém o par de operações simétrico.
