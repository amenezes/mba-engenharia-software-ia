---
name: refactor-arch
description: Analisa, audita e refatora projetos legados para o padrao MVC de forma
  agnostica de tecnologia. Detecta stack e dominio, identifica anti-patterns com
  severidade e arquivo/linha exatos, gera relatorio de auditoria estruturado e
  refatora preservando o funcionamento da aplicacao. Use quando precisar modernizar
  uma codebase para MVC.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash, Edit, Write
---

# refactor-arch

Skill agnostica de tecnologia que executa **3 fases sequenciais** para modernizar
uma codebase para o padrao MVC: **Analise → Auditoria → Refatoracao**.

IMPORTANTE: A skill detecta a stack lendo os manifestos do projeto (requirements.txt,
package.json, etc.). Nunca assuma a linguagem — ela deve funcionar com diferentes
linguagens e frameworks sem qualquer alteracao.

## Fluxo de execucao

Execute as 3 fases EM ORDEM. Cada fase tem um deliveravel concreto e especifico.
Nao avance para a Fase 3 sem confirmacao explicita do humano (obrigatorio).

---

## FASE 1 — Analise do projeto

**Objetivo**: detectar stack, mapear arquitetura atual e imprimir um resumo.

**Passos**:

1. Carregue as heuristicas detalhadas em [references/01-analysis-heuristics.md](references/01-analysis-heuristics.md).
2. Detecte a **linguagem** lendo o manifesto de dependencias do projeto
   (`requirements.txt`, `package.json`, `go.mod`, `pom.xml`, `Cargo.toml`,
   `composer.json`, etc.) e confirmando pela extensao predominante dos arquivos
   fonte. As heuristicas completas estao na referencia.
3. Detecte o **framework e versao exata** lendo o manifesto de dependencias.
4. Detecte o **banco de dados** (driver, ORM, schema/tabelas).
5. Identifique o **dominio da aplicacao** (entidades/recursos) pelos nomes de
   models, tabelas, rotas e collections.
6. Mapeie a **arquitetura atual**:
   - Quantos arquivos fonte existem? Qual o LOC total e por arquivo?
   - Ha separacao de camadas (models/routes/controllers/services)? Elas sao reais
     ou cosmeticas? (Ex: pastas existem mas services nao sao importados?)
   - Liste as **rotas GET publicas** (health, listagens de recursos, etc.) — elas
     serao usadas na validacao da Fase 3, passadas como argumentos ao validate.sh.
7. Conte os arquivos analisados.
8. Antes de imprimir a saida, verifique internamente:
   - [ ] Linguagem detectada corretamente?
   - [ ] Framework e versao conferem com o manifesto?
   - [ ] Dominio descrito corresponde as entidades/tabelas/rotas?
   - [ ] Numero de arquivos condiz com a realidade?

**Saida obrigatoria** — imprima exatamente este bloco (preencha os valores):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <python|javascript|...>
Framework:     <nome + versao exata, ex: Flask 3.1.1>
Dependencies:  <lista das deps principais>
Domain:        <dominio, ex: E-commerce API (produtos, pedidos)>
Architecture:  <descrita, ex: Monolitica — tudo em 4 arquivos>
Source files:  <N> files analyzed
DB tables:     <lista de tabelas/collections>
Endpoints:     <rotas GET publicas, ex: /health, /produtos, /usuarios>
================================
```

Nao modifique nenhum arquivo nesta fase. Apenas leia (Read, Grep, Glob).

---

## FASE 2 — Auditoria de anti-patterns

**Objetivo**: cruzar o codigo contra um catalogo de anti-patterns e gerar um
relatorio estruturado com severidade e `arquivo:linha` exatos.

**Passos**:

1. Carregue o catalogo em [references/02-antipatterns-catalog.md](references/02-antipatterns-catalog.md).
2. Para CADA anti-pattern do catalogo, percorra os arquivos fonte aplicando os
   **sinais de deteccao** descritos. Use Grep com as regex fornecidas e valide
   com leitura contextual (Read) para confirmar e extrair o numero da linha.
3. Para cada achado (finding), registre:
   - Severidade: CRITICAL | HIGH | MEDIUM | LOW
   - Titulo do anti-pattern
   - `File: <caminho>:<linha-inicio>-<linha-fim>` (EXATO)
   - Description: o que foi encontrado
   - Impact: por que importa
   - Recommendation: acao de correcao (link para o playbook)
4. Rejeite falsos positivos: um anti-pattern so conta se houver **>= 2 sinais
   convergentes** (ex: secret = regex de valor hardcoded + nao vem de env + valor
   parece sensivel).
5. Ordene os findings por severidade: **CRITICAL → HIGH → MEDIUM → LOW**.
6. Conte o total por severidade.

**Saida obrigatoria** — gere o relatorio seguindo o template em
[references/03-report-template.md](references/03-report-template.md), incluindo
o cabecalho, o sumario com contagem e a lista de findings ordenada.

Salve uma copia do relatorio em `../reports/audit-project-<N>.md`. O numero do
projeto: pergunte ao humano ou infira pela ordem (1 = primeiro projeto analisado).

**PAUSA OBRIGATORIA** — apos imprimir o relatorio, voce DEVE parar e perguntar:

```
Phase 2 complete. Total: <N> findings (<C> CRITICAL, <H> HIGH, <M> MEDIUM, <L> LOW).
Proceed with refactoring (Phase 3)? [y/n]
```

**NUNCA avance para a Fase 3 sem resposta `y` explicita do humano.** Esta pausa
e obrigatoria por design — o humano deve revisar o relatorio antes de qualquer
modificacao.

---

## FASE 3 — Refatoracao para MVC

**Objetivo**: reestruturar o projeto para o padrao MVC, eliminando os problemas
encontrados, e validar que a aplicacao continua funcionando.

**Passos**:

1. Carregue as diretrizes em [references/04-mvc-guidelines.md](references/04-mvc-guidelines.md)
   (estrutura alvo de camadas) e o playbook em
   [references/05-refactor-playbook.md](references/05-refactor-playbook.md)
   (12 transformacoes concretas com antes/depois).
2. Para CADA finding da Fase 2, aplique a transformacao correspondente do
   playbook. Resolva primeiro os CRITICAL, depois HIGH, MEDIUM e LOW.
3. Crie a estrutura MVC alvo:
   - `config/` — settings carregados de env (sem hardcoded)
   - `models/` — dados + serializacao (sem regras de negocio)
   - camada HTTP fina (`views/`, `routes/`, `resources/`, `handlers/` —
     conforme a convencao de nomenclatura do framework detectado)
   - `controllers/` — orchestracao do fluxo da aplicacao
   - `services/` (quando aplicavel) — regras de negocio extraidas
   - `middlewares/` — error_handler centralizado + auth
   - Entry point claro com factory function (`create_app()`, `createApp()`,
     ou equivalente idiomatico do framework)
4. Preserve **todos os endpoints originais** (mesmas rotas, mesmos verbos, mesmos
   contratos de resposta). A refatoracao nao e rewrite — a API publica nao muda.
5. Rode a validacao automatica, passando como argumentos as **rotas GET publicas**
   mapeadas na Fase 1 (alem de `/health` e `/`, que o script ja testa por padrao):

   ```bash
   bash ${CLAUDE_SKILL_DIR}/scripts/validate.sh <endpoint1> <endpoint2> ...
   # Ex.: validate.sh /produtos /usuarios /pedidos /relatorios/vendas
   ```

   O script detecta o runtime, sobe a aplicacao em background, faz curl em cada
   endpoint (os padrao + os passados como argumentos), verifica os status HTTP e
   derruba a app.

   **FEEDBACK LOOP OBRIGATORIO**: Se o validate.sh falhar, corrija os erros
   e rode novamente. Repita ate obter PASS em todos os cheques. Esta e a
   validacao final da refatoracao — sem PASS, a Fase 3 nao esta concluida.

6. Imprima o resultado:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
<arvore de diretorios criada, usando a saida de `find` ou `tree`>

Validation
  [pass/fail] Application boots without errors
  [pass/fail] All endpoints respond correctly
  [pass/fail] Zero anti-patterns remaining
================================
```

## Regras gerais

- **Agnosticidade**: nunca assuma a linguagem. Detecte pelos manifestos e pela
  extensao dos arquivos fonte. As heuristicas e o playbook cobrem multiplas
  linguagens — use os padroes de deteccao e transformacao correspondentes ao
  ecossistema detectado na Fase 1.
- **Preserve contratos**: rotas, verbos e formatos de resposta originais devem
  continuar funcionando apos a refatoracao.
- **Seja especifico nos sinais**: "codigo ruim" nao conta; `query SQL dentro de
  loop for` conta. Sempre registre `arquivo:linha` exato.
- **Idempotencia parcial**: se a skill for rodada novamente, detecte o que ja foi
  corrigido e nao recrie arquivos existentes.
- **Arquivos de referencia**: carregue-os sob demanda (uma referencia por fase)
  para nao consumir contexto desnecessario.
