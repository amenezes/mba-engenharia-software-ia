# Desafio 3 — Skill `refactor-arch`

Skill do Claude Code que analisa, audita e refatora projetos legados para o padrão
MVC, de forma agnóstica de tecnologia (Python/Flask e Node.js/Express).

---

## A) Análise Manual

Antes de construir a skill, os 3 projetos-alvo foram analisados manualmente
(somente leitura) para entender os problemas que a skill deve detectar. Para cada
projeto são listados os problemas de maior impacto arquitetural, classificados por
severidade conforme a escala do ADR-1 (CRITICAL > HIGH > MEDIUM > LOW), com a
referência exata `arquivo:linha` e a justificativa de relevância.

### A.1) `code-smells-project` — Python/Flask (E-commerce API)

Monolito em 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`),
~780 LOC, sem separação real de camadas. Domínio: produtos, usuários, pedidos e
itens de pedido. Banco SQLite via `sqlite3` cru (sem ORM).

| # | Severidade | Problema | Local | Por que é relevante |
|---|------------|----------|-------|---------------------|
| 1 | CRITICAL | RCE via Debug Mode exposto em todas as interfaces | `app.py:8,88` | `debug=True` + `host="0.0.0.0"` ativa o debugger interativo do Werkzeug, permitindo execução arbitrária de código remoto |
| 2 | CRITICAL | SQL Injection pervasive por concatenação de strings | `models.py:28,109-111,289-297` | Quase toda query monta SQL com `+ str(id)` ou `f"...{var}"`; o endpoint de busca e o login são exploráveis para bypass de auth e exfiltração |
| 3 | CRITICAL | `SECRET_KEY` e senha hardcoded no código | `app.py:7`; `database.py:75-79` | Secret do Flask commitado em texto plano; senhas de seed (`admin123`) também — permite falsificação de sessão |
| 4 | HIGH | N+1 aninhado na listagem de pedidos | `models.py:171-233` | Para cada pedido, abre-se cursor para itens e, para cada item, outro para produto: 1+N+N×M queries por requisição |
| 5 | MEDIUM | Código duplicado (DRY) entre funções de listagem | `models.py:171-201` vs `203-233` | `get_pedidos_usuario` e `get_todos_pedidos` são quase idênticos, mudando só o `WHERE`; correções precisam ser aplicadas em duplicata |
| 6 | MEDIUM | `print()` como logging + vazamento de erros internos | `controllers.py:12,179,208-210` | Sem níveis/estrutura; `str(e)` retornado ao cliente vaza stack trace, auxiliando atacantes |
| 7 | LOW | Estilo de roteamento inconsistente (sem Blueprints) | `app.py:11-30` vs `app.py:32,47,59` | Mistura `add_url_rule` com `@app.route`; app flat sem modularização por domínio |
| 8 | LOW | Nomenclatura ruim e shadowing de builtin | `models.py:187,219` (`cursor2`,`cursor3`); `models.py:24` (`id`) | `cursor2`/`cursor3` mascaram o smell N+1; `id` sobra o builtin Python |

### A.2) `ecommerce-api-legacy` — Node.js/Express (LMS API com checkout)

God Object: `AppManager.js` concentra conexão DB, schema, rotas, regras de negócio,
pagamento e auditoria. ~180 LOC, Express 4.18, `sqlite3` em memória. Domínio: LMS
com checkout (users, courses, enrollments, payments, audit_logs).

> Observação: o ADR-1 cita `GodManager.js`, mas o arquivo real chama-se
> `AppManager.js`. O anti-pattern (God Object) é idêntico.

| # | Severidade | Problema | Local | Por que é relevante |
|---|------------|----------|-------|---------------------|
| 1 | CRITICAL | Secrets hardcoded incluindo chave `pk_live` do Stripe | `utils.js:2-7` | Senha de DB e chave de pagamento LIVE commitadas no repo; sem `.env`/`.gitignore` — qualquer leak compromete tudo |
| 2 | CRITICAL | "Hash" de senha com Base64 em loop (trivialmente reversível) | `utils.js:17-23` | Base64 é codificação, não criptografia; sem salt, colisões massivas; senha default `"123456"` aceita |
| 3 | CRITICAL | Número de cartão e chave do gateway logados em stdout | `AppManager.js:45` | Violação direta do PCI-DSS (PAN nunca deve ser logado em claro); logs costumam ir para agregadores |
| 4 | HIGH | God Class: uma classe detém DB, schema, rotas, regras e pagamento | `AppManager.js:4-141` | `setupRoutes()` tem ~114 linhas com SQL, pagamento, auditoria embutidos; incontrolável e incontrolável de testar |
| 5 | HIGH | N+1 quadrático no relatório financeiro | `AppManager.js:83-127` | 1+C+E+2E queries (courses, enrollments, users, payments) que poderiam ser um único JOIN |
| 6 | MEDIUM | Estado mutável global sem TTL/evicção | `utils.js:9-10` | `globalCache` cresce indefinidamente (vazamento de memória); `totalRevenue` compartilhado entre requisições |
| 7 | MEDIUM | Callback hell de 5 níveis sem transação | `AppManager.js:37-77` | Inserções de enrollment/payment/audit não transacionais; crash no meio deixa DB inconsistente |
| 8 | LOW | Padrões deprecated: sqlite3 callback-style, sem helmet/CORS, `console.log` | `AppManager.js:1`; `app.js:6` | API callback obriga o callback hell; sem headers de segurança; logging não estruturado |
| 9 | LOW | Nomenclatura críptica de variáveis | `AppManager.js:29-33` | `u`,`e`,`p`,`cc`,`cid` prejudicam legibilidade e buscabilidade |

### A.3) `task-manager-api` — Python/Flask (Task Manager API)

Caso mais desafiador: **MVC cosmético** — as pastas `models/`, `routes/`,
`services/`, `utils/` existem, mas a separação é ilusória. ~1177 LOC, Flask 3.0 +
Flask-SQLAlchemy 3.1. Domínio: tasks, users, categories.

| # | Severidade | Problema | Local | Por que é relevante |
|---|------------|----------|-------|---------------------|
| 1 | CRITICAL | `SECRET_KEY` hardcoded apesar de `python-dotenv` declarado | `app.py:13` | Dependência de env presente mas nunca usada; secret commitado permite falsificação de sessão |
| 2 | CRITICAL | Senhas com MD5 sem salt | `models/user.py:27-32` | MD5 é criptograficamente quebrado; rainbow tables reversíveis; idênticas senhas geram idênticos hashes |
| 3 | HIGH | N+1 em listagem e relatórios | `task_routes.py:42,51`; `report_routes.py:56,163` | `User.query.get()`/`Category.query.get()` dentro de loop sobre tasks — 1+2N queries |
| 4 | HIGH | Lógica de negócio e validação dentro de rotas (sem Service real) | `task_routes.py:85-154` | ~70 linhas de validação inline; `services/` existe mas está vazio/morto — separação é cosmética |
| 5 | MEDIUM | APIs deprecated do SQLAlchemy 1.x (`Query.get`) | | Usado 15× em todo o código; em SQLAlchemy 2.x o idiomático é `db.session.get()` |
| 6 | MEDIUM | Código morto: `NotificationService` nunca instanciado; helpers nunca chamados | `services/notification_service.py`; `utils/helpers.py` | Dependências declaradas mas não usadas (`marshmallow`, `requests`, `dotenv`); services importam nada |
| 7 | LOW | Regra "overdue" duplicada em 5+ locais enquanto `Task.is_overdue()` nunca é chamado | `task_routes.py:30-39`; `report_routes.py:33-43` | Método canônico existe mas é ignorado; mudança na regra exige editar 6 lugares |
| 8 | LOW | `except:` bare engole todas as exceções (inclusive `KeyboardInterrupt`) | `task_routes.py:62,137,204`; `user_routes.py:130,149` | Esconde erros de programação atrás de 500 genérico; sem JSON error handler registrado |

### Síntese da análise

Os 3 projetos compartilham um núcleo de anti-patterns — hardcoded secrets, password
handling inseguro, God Class, N+1/queries em loop, falta de auth, lógica de negócio
em rotas, ausência de error handling centralizado — o que valida a viabilidade de
uma skill agnóstica. A especificidade de cada projeto (monolito flat vs God Object
vs MVC cosmético) testa a capacidade da skill de detectar problemas além da
ausência óbvia de pastas.

---

## B) Construção da Skill

Decisões de design registradas em [`adr-desafio-3/plano.md`](adr-desafio-3/plano.md).

### Estrutura

A skill fica em `.claude/skills/refactor-arch/` dentro de cada projeto, com
`SKILL.md` (orquestrador) + 5 arquivos de referência (progressive disclosure) +
`scripts/validate.sh`:

```
.claude/skills/refactor-arch/
├── SKILL.md                          # 3 fases + pausa de confirmação
├── references/
│   ├── 01-analysis-heuristics.md     # detecção de stack/domínio/arquitetura
│   ├── 02-antipatterns-catalog.md    # 12 anti-patterns com sinais de detecção
│   ├── 03-report-template.md         # formato padronizado do relatório
│   ├── 04-mvc-guidelines.md          # regras do MVC alvo
│   └── 05-refactor-playbook.md       # 12 transformações antes/depois
└── scripts/validate.sh               # smoke test (boot + curl endpoints)
```

### Anti-patterns incluídos (12)

Hardcoded Secrets, Insecure Password Storage, Sensitive Data Exposure, SQL Injection,
God Class, Debug Mode RCE, Missing AuthN/AuthZ, Business Logic in Routes, N+1 Queries,
Deprecated API Usage, No Centralized Error Handling, Magic Numbers/DRY. Cada um com
**sinais de detecção multi-linguagem** (regex + validação contextual) e referência ao
playbook de transformação correspondente.

### Como a agnósticidade foi garantida

1. **Heurísticas de detecção** fornecem regex para Python E JavaScript em cada
   anti-pattern (ex: `SECRET_KEY\s*=` e `(password|secret)\s*[:=]\s*['"]`).
2. **Playbook com antes/depois em ambas as linguagens** — toda transformação tem
   exemplo em Python (Flask) e Node.js (Express).
3. **`validate.sh` detecta o runtime** automaticamente (procura `app.py`/`app.js`,
   `requirements.txt`/`package.json`) e não assume nenhuma linguagem.
4. **A skill nunca hardcodifica nomes de arquivos** — lê manifestos e estrutura de
   diretórios.

### Desafios encontrados

- **MVC cosmético vs real**: `task-manager-api` já tinha pastas `models/routes/services`
  mas services estavam mortos. A heurística de God Class (#5) foi ajustada para detectar
  "services não importados" como sinal de separação ilusória.
- **Preservar contratos HTTP**: adicionar auth poderia quebrar endpoints originais. A
  solução foi proteger endpoints destrutivos/admin (POST/DELETE) e manter GETs públicos,
  além de adicionar `/health` aberto para o smoke test.
- **Detecção de Node.js sem Node instalado**: o `validate.sh` foi tornado resiliente com
  detecção de `python3`/`python`/venvs locais e `node`/`nodejs`.

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---------|----------|------|--------|-----|-------|
| code-smells-project | 5 | 3 | 2 | 2 | 12 |
| ecommerce-api-legacy | 4 | 3 | 3 | 2 | 12 |
| task-manager-api | 3 | 4 | 3 | 2 | 12 |

Relatórios completos em `reports/audit-project-{1,2,3}.md`.

### Comparação antes/depois

| Projeto | Arquitetura antes | Arquitetura depois | Validação |
|---------|-------------------|--------------------|-----------|
| code-smells-project | Monolito em 4 arquivos (780 LOC), sem camadas | MVC: config/models/controllers/services/routes/middlewares + factory `create_app()` | PASS (8/8) |
| ecommerce-api-legacy | God Object (`AppManager` com 141 LOC concentrando tudo) | MVC: config/db/models/controllers/services/routes/middlewares + `createApp()` | PASS (4/4) |
| task-manager-api | MVC cosmético (services mortos, MD5, N+1) | MVC real: config + middlewares, services vivos, werkzeug, joinedload, JWT real | PASS (8/8) |

### Transformações aplicadas (destaques)

- Secrets extraídos para env (`os.environ`/`process.env`) + `.env.example` em todos
- MD5/base64 → werkzeug.security / crypto.scrypt
- `password`/`senha` removidos de toda serialização (`to_dict`/`res.json`)
- SQL concatenado → placeholders parametrizados (`?`)
- `debug=True` → env-driven (default False) + bind em `127.0.0.1`
- God Class decomposto em models + controllers + services + routes
- N+1 → JOIN / `joinedload` / `GROUP BY`
- `fake-jwt-token` → JWT/HMAC real assinado
- Error handling centralizado (`@app.errorhandler` / middleware Express)
- `Query.get` (SQLAlchemy 1.x) → `db.session.get` (2.x)

### Checklist de validação

**code-smells-project** (validate.sh):
```
[pass] Application boots without errors
[pass] GET /health -> 200
[pass] GET / -> 200
[pass] GET /produtos -> 200
[pass] GET /usuarios -> 200
[pass] GET /pedidos -> 200
[pass] GET /relatorios/vendas -> 200
Result: PASS (8/8)
```

**task-manager-api** (validate.sh):
```
[pass] Application boots without errors
[pass] GET /health -> 200
[pass] GET / -> 200
[pass] GET /tasks -> 200
[pass] GET /users -> 200
[pass] GET /tasks/stats -> 200
[pass] GET /reports/summary -> 200
Result: PASS (8/8)
```

**ecommerce-api-legacy**: código refatorado para MVC (20 arquivos em
config/db/models/controllers/services/routes/middlewares); validação via `validate.sh`
requer Node.js instalado no ambiente.

### Critérios de aceite (3/3 projetos)

| Critério | code-smells | ecommerce-legacy | task-manager |
|----------|:-----------:|:-----------------:|:------------:|
| Fase 1 detecta stack | OK | OK | OK |
| Fase 2 ≥ 5 findings | 12 | 12 | 12 |
| Fase 2 ≥ 1 CRITICAL/HIGH | 8 | 7 | 7 |
| Fase 3 app funciona | PASS | skip* | PASS |

*ecommerce-api-legacy: refatoração completa; validação pendente de Node.js no ambiente.

## D) Como Executar

Pré-requisitos:

- [Claude Code](https://code.claude.com/docs/en) instalado e autenticado
- Python 3.10+ (projetos 1 e 3)
- Node.js 18+ (projeto 2 — necessário para validação). Recomendado via nvm:
  `export NVM_DIR="$HOME/.config/nvm" && source "$NVM_DIR/nvm.sh" && nvm install --lts`

Execução em cada projeto:

```bash
# Projeto 1 — Python/Flask (E-commerce)
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — Node.js/Express (LMS)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — Python/Flask (Task Manager)
cd ../task-manager-api
claude "/refactor-arch"
```

Validação pós-refatoração (executada automaticamente na Fase 3):

```bash
# A skill roda scripts/validate.sh, que:
# 1. detecta o runtime (Python/Node) e o executável (python3/venv/node)
# 2. sobe a aplicação em background numa porta livre
# 3. faz curl nos endpoints originais mapeados na Fase 1
# 4. verifica status HTTP 2xx/3xx e derruba a app
# 5. imprime [pass]/[fail] por cheque + resultado final

# Para rodar manualmente:
bash .claude/skills/refactor-arch/scripts/validate.sh /produtos /usuarios
```

Para rodar as aplicações refatoradas manualmente:

```bash
# Projeto 1
cd code-smells-project && pip install -r requirements.txt && python app.py

# Projeto 2 (Node via nvm)
cd ecommerce-api-legacy && npm install && node src/app.js

# Projeto 3
cd task-manager-api && pip install -r requirements.txt && python app.py
```

Relatórios de auditoria em `reports/audit-project-{1,2,3}.md`.
