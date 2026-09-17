# Fase 23 — Gradle: Criar Projeto — Design

## Reaproveitamento quase total: nada novo no writer

Diferente de todas as fatias anteriores, `create_project` não precisou de nenhum método novo em `GradleWriter` — `create_build_file` (Fase 21) já sabia montar um `build.gradle` do zero a partir de `packaging`/`group_id`/`version`/`dependencies`, que é exatamente a forma de um `ModuleManifest`. `create_project` só orquestra: escreve `settings.gradle` diretamente (texto simples, sem precisar de `add_include` — a lista inteira de submódulos já é conhecida de uma vez, então não há "anexar a uma lista existente" a fazer) e chama `create_build_file` uma vez por módulo (raiz + cada submódulo).

## `_validate_gradle_manifest`: a mesma validação, menos uma regra

Comparado a `MavenAdapter._validate_maven_manifest`, a única diferença é a ausência da checagem "`is_root and (not group_id or not version)` → erro". Essa regra existe no Maven porque o pom raiz não tem `<parent>` — sem ela, um módulo raiz sem `groupId`/`version` próprios ficaria com esses campos vazios no XML, o que é inválido. No Gradle, um `build.gradle` sem `group`/`version` é perfeitamente válido (só significa que o projeto não declara essas coordenadas) — o próprio `set_scalar`/`create_build_file` já lidam com `group_id`/`version` `None` naturalmente (omitem a linha). As outras duas regras (packaging-pom-obrigatório-para-submódulos-ou-BOM, dependência-gerenciada-precisa-de-version) são idênticas e mantidas como uma pequena duplicação deliberada em vez de extração — mesmo raciocínio já registrado na Fase 17 para o guard de packaging/BOM/submódulos de `update_metadata`.

## Materialização de diretórios: sem registro de build

`_materialize_directories` (novo, privado de `GradleAdapter`) é uma versão simplificada do equivalente Maven: cria (ou copia de `source_root`, se houver arquivo real) cada diretório de `DirectoryStructure`, mas nunca chama nada equivalente a `register_directory_role` — esse mecanismo (`sourceSets{}`) está fora de escopo da feature inteira, não só desta fase. Um diretório "não-convencional" listado no manifesto é criado normalmente, só não aparece com o sufixo `(build)` no Painel [5] (que depende de o build de fato declarar o diretório, coisa que o Gradle desta feature não faz).

## Escolha de dialeto: sempre Groovy

`ModuleManifest` é, por design desde a Fase 6, uma representação agnóstica de build tool — não tem (e não deveria ganhar aqui) um campo dizendo "isso é Kotlin DSL". `create_project` sempre escreve `build.gradle`/`settings.gradle` (Groovy). Isso é diferente de `add_module` (Fase 21), que herda o dialeto do projeto Gradle *já existente* (ali há um `settings.gradle(.kts)` real para consultar); aqui não há projeto anterior nenhum — a única fonte de verdade disponível é o manifesto, que não opina sobre dialeto. Se o usuário quiser um projeto Kotlin DSL a partir de um manifesto, a única forma hoje é `create_project` (Groovy) seguido de conversão manual — fora de escopo, documentado como limitação consciente.

## Escopo de aninhamento: um nível, igual ao Maven

Nenhum teste de `MavenAdapter.create_project` exercita netos (submódulo de submódulo) — o próprio Maven só materializa recursivamente através de `_materialize`, mas na prática (e nos testes) sempre raiz → filhos diretos. Para o Gradle, ir além de um nível esbarraria de novo na árvore achatada da Fase 15 (um manifesto com netos precisaria decidir se os achata como `include` de segundo nível, com paths tipo `:pai:filho`, contrariando a modelagem "todo incluído é filho direto da raiz"). Como o Maven em si não testa/exige mais que um nível, `create_project` do Gradle mantém exatamente o mesmo escopo: `manifest.submodules` viram filhos diretos; submódulos de submódulos no manifesto, se existirem, não são percorridos.

## Testes

`tests/test_gradle_adapter_create_project.py`: módulo único, multi-módulo (dois submódulos), BOM com dependência gerenciada/direta convivendo, criação de diretórios customizados, nomes duplicados/dependência-sem-version/packaging-inconsistente rejeitados (mesmas mensagens do Maven), raiz **sem** group/version **aceita** (diferença deliberada do Maven, testada explicitamente), destino não-vazio rejeitado/vazio aceito, `source_root` copiando arquivo real e caindo para `mkdir` quando não há snapshot correspondente, e resultado batendo com reinferência do zero.
