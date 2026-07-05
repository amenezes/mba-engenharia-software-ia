# 02 — catálogo de Anti-Patterns

Catálogo de **12 anti-patterns** com sinais de detecção, classificação de
Severidade e referência ao playbook de transformação.

**Princípio de Agnosticidade**: Os anti-patterns abaixo descrevem **padrões de
problema** independentes de linguagem ou framework. Os sinais de detecção
concretos são fornecidos para Python e Node.js (escopo do desafio); para outras
linguagens, aplique os mesmos princípios usando os construtos equivalentes do
ecossistema. O que importa e o *padrão* (ex: "atribuição de valor literal a
variável de configuração sensível sem leitura de mecanismo de injeção de
ambiente"), não a sintaxe específica.

## Como usar

Para cada anti-pattern abaixo:

1. Aplique os **sinais de detecção** (regex + leitura contextual) nos arquivos fonte.
2. Confirme com **>= 2 sinais convergentes** antes de registrar (evita falso positivo).
3. Extraia o `arquivo:linha` exato (use Grep com `-n`).
4. Registre o finding no relatório com severidade, descrição, impacto e recomendação.

Ordem de sev: **CRITICAL > HIGH > MEDIUM > LOW**.

---

## 1. Hardcoded Secrets [CRITICAL]

**Sinais de detecção**:

- Grep (Python): `SECRET_KEY\s*=\s*['"]` ou `app\.config\['SECRET_KEY'\]\s*=`
- Grep (Node): `(password|passwd|secret|api_key|apiKey|token)\s*[:=]\s*['"][^'"]{6,}['"]`
- Chaves com prefixo suspeito: `pk_live_`, `sk_live_`, `sk_`, `AKIA` (AWS)
- JWT/secret com valor literal: `fake-jwt`, `super-secret`, `minha-chave`
- Confirmar: o valor NÃO vem de `os.environ` / `process.env` / `os.getenv`

**Impacto**: permite falsificacao de sessão, acesso não autorizado a serviços
externos (pagamento, email), comprometimento total em caso de leak do repo.

**Transformação**: [Playbook #1 — Extrair secrets para env](05-refactor-playbook.md#1-extrair-secrets-para-env)

---

## 2. Insecure Password Storage [CRITICAL]

**Sinais de detecção**:

- Grep: `hashlib\.md5\(`, `hashlib\.sha1\(`, `Buffer\.from\(.*\)\.toString\(['"]base64`
- Grep: `badCrypto`, função custom de "hash" com loop + base64
- Compare em texto plano: `senha ==`, `password ==`, `\.password ===`
- Confirmar: AUSÊNCIA de `bcrypt`, `argon2`, `werkzeug.security`,
  `generate_password_hash`, `crypto.scrypt`, `crypto.pbkdf2`

**Impacto**: senhas trivialmente reversiveis (MD5/base64 sem salt); rainbow tables;
credenciais comprometidas em caso de leak do banco.

**Transformação**: [Playbook #2 — Hash de senha seguro](05-refactor-playbook.md#2-hash-de-senha-seguro)

---

## 3. Sensitive Data Exposure [CRITICAL]

**Sinais de detecção**:

- Grep em methods de serialização: `to_dict\(`, `to_json\(`, `serialize\(`
  contendo `password`, `senha`, `pass`, `secret`, `token`
- Grep em respostas: `res\.(json|send)\(` ou `jsonify\(` construindo dict com
  `senha`/`password`
- Grep em logs: `print\(.*senha`, `console\.log\(.*card|cc|pan|password`,
  `console\.log\(.*paymentGatewayKey`
- Confirmar: o campo sensível aparece no payload retornado ao cliente OU logado

**Impacto**: vazamento de PII / hashes de senha / PAN (viola PCI-DSS) para qualquer
cliente ou operador de logs.

**Transformação**: [Playbook #3 — Remover campos sensíveis](05-refactor-playbook.md#3-remover-campos-sensíveis-da-serialização)

---

## 4. SQL Injection [CRITICAL]

**Sinais de detecção**:

- Grep (Python): `execute\(\s*['"].*\+`, `execute\(\s*f['"]`, `execute\(['"].*%s.*%\s*`,
  `cursor\.execute\(['"]SELECT.*\{` (f-string)
- Grep (Node): `db\.run\(\s*\``, `db\.exec\(\s*\``, template literal com `${}` em SQL
- concatenação direta: `"SELECT.*" \+ str\(`, `"SELECT.*" \+ req\.body`
- Confirmar: a query NÃO usa placeholders parametrizados (`?` ou `%s` com args)

**Atenção**: queries com `?`/`[params]` NÃO são SQL Injection — são parametrizadas.
Não confunda SQL cru embutido em rota (anti-pattern #8) com injeção.

**Impacto**: bypass de autenticação, exfiltracao de dados, DROP/ALTER arbitrario,
RCE via DB em alguns SGBDs.

**Transformação**: [Playbook #4 — Parametrizar queries](05-refactor-playbook.md#4-parametrizar-queries)

---

## 5. God Class / God Method [CRITICAL]

**Sinais de detecção**:

- Arquivo fonte com **> 200 LOC** misturando responsabilidades (DB + regras + rotas)
- Função/método com **> 50 LOC** e multiplas responsabilidades (validação + DB + resposta)
- Classe com nome `*Manager*`, `*Controller*` que registra rotas E acessa DB E tem
  regras de negocio (ex: `setupRoutes` dentro da classe)
- Grep: `class .*(Manager|God|Everything)` + presença de `app\.(get|post)` no mesmo arquivo
- Confirmar: o mesmo arquivo importa driver DB E define rotas E contem regras

**Impacto**: impossível testar em isolamento, mudanca em um ponto afeta tudo,
violacao do Single Responsibility Principle.

**Transformação**: [Playbook #6 — Decompor God Class](05-refactor-playbook.md#6-decompor-god-class)

---

## 6. Debug Mode RCE / Insecure Bind [HIGH]

**Sinais de detecção**:

- Grep: `app\.run\(.*debug\s*=\s*True`, `debug=True`
- Grep: `host\s*=\s*['"]0\.0\.0\.0['"]`, `app\.config\['DEBUG'\]\s*=\s*True`
- Confirmar: `debug=True` esta no `app.run()` ou config (ativa debugger Werkzeug)

**Impacto**: o debugger interativo do Werkzeug permite execução arbitrária de
código Python remoto — RCE direto.

**Transformação**: [Playbook #5 — Desligar debug + factory](05-refactor-playbook.md#5-desligar-debug--factory-create_app)

---

## 7. Missing AuthN/AuthZ [HIGH]

**Sinais de detecção**:

- Rotas `/admin/`, `DELETE`, `PUT`/`PATCH` sem decorator/middleware de auth:
  - Python: ausência de `@login_required`, `@jwt_required`, `@requires_auth`
  - Node: ausência de middleware (`protect`, `authenticate`, `verifyToken`) na cadeia
- Endpoint `/login` ou `/auth` que NÃO emite token verificavel:
  - retorna `'fake-jwt'`, string concatenada `'token-' + id`, ou não retorna token
- ausência total de import de `jwt`, `flask-login`, `passport`, `express-jwt`
- Confirmar: rota sensível (admin/delete/write) acessível sem credencial

**Impacto**: escalonamento vertical/horizontal, qualquer cliente anonimo altera
dados privilegiados, bypass total de controle de acesso.

**Transformação**: [Playbook #7 — Camada de autenticação](05-refactor-playbook.md#7-adicionar-camada-de-autenticação)

---

## 8. Business Logic in Routes/Controllers [HIGH]

**Sinais de detecção**:

- Grep em arquivos de rota/controller por: calculos de desconto, regras de
  pagamento, dispatch de notificação (email/sms/push), loops de validação complexos
- Grep: `print\(.*ENVIANDO (EMAIL|SMS|PUSH)`, `console\.log\(.*notificação`
- presença de `if .* desconto`, `if .* status === 'PAID'`, regra de negocio inline
- validação manual longa (`if "x" not in dados` repetido) dentro de handler HTTP
- Confirmar: a regra de negocio esta no handler, não em um service/model

**Impacto**: regras de negocio acopladas ao transporte HTTP; impossível testar
isoladamente, difícil de manter e evoluir.

**Transformação**: [Playbook #8 — Mover lógica para Services](05-refactor-playbook.md#8-mover-lógica-de-negocio-para-services)

---

## 9. N+1 / Queries in Loops [HIGH]

**Sinais de detecção**:

- Grep: loop (`for .* in`, `.forEach`, `.map`) contendo chamada de query:
  - Python: `\.query\.get\(`, `\.query\.filter`, `cursor\.execute\(`, `db\.session\.`
  - Node: `db\.(get|all|run)\(`, `\.findById\(`, `\.findOne\(` dentro de loop
- Contagem agregada feita em Python/JS (`for t in tasks: if t.done: count+=1`)
  em vez de `COUNT(*)` / `GROUP BY` no SQL
- Confirmar: ha um acesso ao DB dentro do corpo de um loop

**Impacto**: degradação quadratica/cubica de performance; 1+N+N*M queries por
requisicao; não escala.

**Transformação**: [Playbook #9 — Resolver N+1](05-refactor-playbook.md#9-resolver-n1-com-join--joinedload--group-by)

---

## 10. Deprecated API Usage [MEDIUM]

**Sinais de detecção**:

- SQLAlchemy 1.x: `\.query\.get\(` (legacy), `Query.get` (usar `db.session.get()`)
- Python: `flask\.ext\.`, `flask\.Markup`, `app\.run` em producao sem WSGI server
- Node: `require\(['"]body-parser['"]\)` (deprecated, use `express.json()`)
- Node: `sqlite3.*\.verbose\(\)` (logging ruidoso), callback-style sem Promise
- Node: `app\.listen` sem error handler / graceful shutdown
- Confirmar: a API esta marcada como legacy/deprecated na doc oficial da versão instalada

**Impacto**: quebra em upgrades, bugs conhecidos, código fora do idiomático atual,
dificuldade de manutenção.

**Transformação**: [Playbook #11 — Migrar APIs deprecated](05-refactor-playbook.md#11-migrar-apis-deprecated)

---

## 11. No Centralized Error Handling [MEDIUM]

**Sinais de detecção**:

- Grep: `except:\s*$`, `except Exception` seguido de `pass` ou `return str(e)`
- Grep (Node): `catch\s*\(\s*\)` vazio, `err => \{` seguido de nada, `err => \{\}`
- ausência de `@app\.errorhandler` (Python) / middleware `(err, req, res, next)`
  (Node)
- `return str(e)` ou `res\.send\(.*err\)` vazando detalhes internos
- Confirmar: não existe handler central de erros registrado no app

**Impacto**: erros 500 com stack trace vazado, comportamento inconsistente,
sem observabilidade, facilita ataque por revelacao de informação.

**Transformação**: [Playbook #10 — Centralizar error handling](05-refactor-playbook.md#10-centralizar-error-handling)

---

## 12. Magic Numbers/Strings + DRY [LOW]

**Sinais de detecção**:

- Literais numericos magicos: `if .* > 10000`, `for .* < 10000`, `0\.1[0-9]*`
  sem `CONST`/`Enum`
- Strings magicas repetidas: `"PAID"`, `"DENIED"`, `"pending"` em > 2 locais
- Grep por status repetido: `['"](PAID|DENIED|done|pending|in_progress)['"]`
- Blocos duplicados (DRY): funções com > 70% de similaridade
  - Ex: `get_pedidos_usuario` vs `get_todos_pedidos` (mudam só o WHERE)
  - Ex: lógica "overdue" em 5+ arquivos
- Confirmar: o literal aparece repetido sem extracao para constante, OU existem
  blocos quase identicos

**Impacto**: regras de negocio opacas, risco de inconsistencia ao mudar em um
lugar só, dificuldade de manutenção.

**Transformação**: [Playbook #12 — Extrair constantes + eliminar duplicação](05-refactor-playbook.md#12-extrair-constantesenums--eliminar-duplicação)
