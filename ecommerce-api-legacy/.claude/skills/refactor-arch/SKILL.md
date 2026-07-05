---
name: refactor-arch
description: Analisa, audita e refatora projetos legados para o padrão MVC de forma
  agnóstica de tecnologia. Detecta stack e domínio, identifica anti-patterns com
  severidade e arquivo/linha exatos, gera relatório de auditoria estruturado e
  refatora preservando o funcionamento da aplicação. Use quando precisar modernizar
  uma codebase para MVC.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash, Edit, Write
---

# refactor-arch

Skill agnóstica de tecnologia que executa **3 fases sequenciais** para modernizar
uma codebase para o padrão MVC: **Análise → Auditoria → Refatoração**.

IMPORTANTE: A skill detecta a stack lendo os manifestos do projeto (requirements.txt,
package.json, etc.). Nunca assuma a linguagem — ela deve funcionar com diferentes
linguagens e frameworks sem qualquer alteração.

## Fluxo de execução

Execute as 3 fases EM ORDEM. Cada fase tem um deliverável concreto e específico.
Não avance para a Fase 3 sem confirmação explícita do humano (obrigatório).

---

## FASE 1 — Análise do projeto

**Objetivo**: detectar stack, mapear arquitetura atual e imprimir um resumo.

**Passos**:

1. Carregue as heurísticas detalhadas em [references/01-analysis-heuristics.md](references/01-analysis-heuristics.md).
2. Detecte a **linguagem** lendo o manifesto de dependências do projeto
   (`requirements.txt`, `package.json`, `go.mod`, `pom.xml`, `Cargo.toml`,
   `composer.json`, etc.) e confirmando pela extensão predominante dos arquivos
   fonte. As heurísticas completas estão na referência.
3. Detecte o **framework e versão exata** lendo o manifesto de dependências.
4. Detecte o **banco de dados** (driver, ORM, schema/tabelas).
5. Identifique o **domínio da aplicação** (entidades/recursos) pelos nomes de
   models, tabelas, rotas e collections.
6. Mapeie a **arquitetura atual**:
   - Quantos arquivos fonte existem? Qual o LOC total e por arquivo?
   - Ha separação de camadas (models/routes/controllers/services)? Elas são reais
     ou cosmeticas? (Ex: pastas existem mas services não são importados?)
   - Liste as **rotas GET Públicas** (health, listagens de recursos, etc.) — elas
     serao usadas na validação da Fase 3, passadas como argumentos ao validate.sh.
7. Conte os arquivos analisados.
8. Antes de imprimir a saída, verifique internamente:
   - [ ] Linguagem detectada corretamente?
   - [ ] Framework e versão conferem com o manifesto?
   - [ ] domínio descrito corresponde as entidades/tabelas/rotas?
   - [ ] número de arquivos condiz com a realidade?

**Saída obrigatória** — imprima exatamente este bloco (preencha os valores):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <python|javascript|...>
Framework:     <nome + versão exata, ex: Flask 3.1.1>
Dependencies:  <lista das deps principais>
Domain:        <domínio, ex: E-commerce API (produtos, pedidos)>
Architecture:  <descrita, ex: Monolitica — tudo em 4 arquivos>
Source files:  <N> files analyzed
DB tables:     <lista de tabelas/collections>
Endpoints:     <rotas GET Públicas, ex: /health, /produtos, /usuarios>
================================
```

Não modifique nenhum arquivo nesta fase. Apenas leia (Read, Grep, Glob).

---

## FASE 2 — Auditoria de anti-patterns

**Objetivo**: cruzar o código contra um catálogo de anti-patterns e gerar um
relatório estruturado com severidade e `arquivo:linha` exatos.

**Passos**:

1. Carregue o catálogo em [references/02-antipatterns-catalog.md](references/02-antipatterns-catalog.md).
2. Para CADA anti-pattern do catálogo, percorra os arquivos fonte aplicando os
   **sinais de detecção** descritos. Use Grep com as regex fornecidas e valide
   com leitura contextual (Read) para confirmar e extrair o número da linha.
3. Para cada achado (finding), registre:
   - severidade: CRITICAL | HIGH | MEDIUM | LOW
   - título do anti-pattern
   - `File: <caminho>:<linha-inicio>-<linha-fim>` (EXATO)
   - Description: o que foi encontrado
   - Impact: por que importa
   - Recommendation: ação de correção (link para o playbook)
4. Rejeite falsos positivos: um anti-pattern só conta se houver **>= 2 sinais
   convergentes** (ex: secret = regex de valor hardcoded + não vem de env + valor
   parece sensível).
5. Ordene os findings por severidade: **CRITICAL → HIGH → MEDIUM → LOW**.
6. Conte o total por severidade.

**Saída obrigatória** — gere o relatório seguindo o template em
[references/03-report-template.md](references/03-report-template.md), incluindo
o cabeçalho, o sumário com contagem e a lista de findings ordenada.

Salve uma cópia do relatório em `../reports/audit-project-<N>.md`. O número do
projeto: pergunte ao humano ou infira pela ordem (1 = primeiro projeto analisado).

**PAUSA OBRIGATÓRIA** — após imprimir o relatório, voce DEVE parar e perguntar:

```
Phase 2 complete. Total: <N> findings (<C> CRITICAL, <H> HIGH, <M> MEDIUM, <L> LOW).
Proceed with refactoring (Phase 3)? [y/n]
```

**NUNCA avance para a Fase 3 sem resposta `y` explícita do humano.** Esta pausa
e obrigatória por design — o humano deve revisar o relatório antes de qualquer
modificação.

---

## FASE 3 — refatoração para MVC

**Objetivo**: reestruturar o projeto para o padrão MVC, eliminando os problemas
encontrados, e validar que a aplicação continua funcionando.

**Passos**:

1. Carregue as diretrizes em [references/04-mvc-Guidelines.md](references/04-mvc-Guidelines.md)
   (estrutura alvo de camadas) e o playbook em
   [references/05-refactor-playbook.md](references/05-refactor-playbook.md)
   (12 transformacoes concretas com antes/depois).
2. Para CADA finding da Fase 2, aplique a transformação correspondente do
   playbook. Resolva primeiro os CRITICAL, depois HIGH, MEDIUM e LOW.
3. Crie a estrutura MVC alvo:
   - `config/` — settings carregados de env (sem hardcoded)
   - `models/` — dados + serialização (sem regras de negocio)
   - camada HTTP fina (`views/`, `routes/`, `resources/`, `handlers/` —
     conforme a convenção de nomenclatura do framework detectado)
   - `controllers/` — orchestracao do fluxo da aplicação
   - `services/` (quando aplicável) — regras de negocio extraidas
   - `middlewares/` — error_handler centralizado + auth
   - Entry point claro com factory function (`create_app()`, `createApp()`,
     ou equivalente idiomático do framework)
4. Preserve **todos os endpoints originais** (mesmas rotas, mesmos verbos, mesmos
   contratos de resposta). A refatoração não e rewrite — a API pública não muda.
5. Rode a validação automática, passando como argumentos as **rotas GET Públicas**
   mapeadas na Fase 1 (alem de `/health` e `/`, que o script já testa por padrão):

   ```bash
   bash ${CLAUDE_SKILL_DIR}/scripts/validate.sh <endpoint1> <endpoint2> ...
   # Ex.: validate.sh /produtos /usuarios /pedidos /relatórios/vendas
   ```

   O script detecta o runtime, sobe a aplicação em background, faz curl em cada
   endpoint (os padrão + os passados como argumentos), verifica os status HTTP e
   derruba a app.

   **FEEDBACK LOOP OBRIGATÓRIO**: Se o validate.sh falhar, corrija os erros
   e rode novamente. Repita até obter PASS em todos os cheques. Esta e a
   validação final da refatoração — sem PASS, a Fase 3 não esta concluida.

6. Imprima o resultado:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
<arvore de diretórios criada, usando a saída de `find` ou `tree`>

Validation
  [pass/fail] Application boots without errors
  [pass/fail] All endpoints respond correctly
  [pass/fail] Zero anti-patterns remaining
================================
```

## Regras gerais

- **Agnosticidade**: nunca assuma a linguagem. Detecte pelos manifestos e pela
  extensão dos arquivos fonte. As heurísticas e o playbook cobrem multiplas
  linguagens — use os padrões de detecção e transformação correspondentes ao
  ecossistema detectado na Fase 1.
- **Preserve contratos**: rotas, verbos e formatos de resposta originais devem
  continuar funcionando após a refatoração.
- **Seja específico nos sinais**: "código ruim" não conta; `query SQL dentro de
  loop for` conta. Sempre registre `arquivo:linha` exato.
- **Idempotencia parcial**: se a skill for rodada novamente, detecte o que já foi
  corrigido e não recrie arquivos existentes.
- **Arquivos de referência**: carregue-os sob demanda (uma referência por fase)
  para não consumir contexto desnecessário.
