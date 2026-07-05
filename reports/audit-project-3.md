================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Files:   12 analyzed | ~1177 lines of code

Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 3 | LOW: 2

Findings

[CRITICAL] Hardcoded Secrets
File: app.py:13; services/notification_service.py:9-10
Description: SECRET_KEY = 'super-secret-key-123' commitada apesar de python-dotenv
             estar declarado em requirements.txt:6 (nunca importado). Credenciais SMTP
             ('taskmanager@gmail.com' / 'senha123') tambem hardcoded no NotificationService.
Impact: Permite falsificacao de sessao Flask e comprometimento da conta de email.
Recommendation: Mover para os.environ via dotenv + .env.example (Playbook #1).

[CRITICAL] Insecure Password Storage
File: models/user.py:29,32
Description: set_password e check_password usam hashlib.md5 — MD5 e criptograficamente
             quebrado, sem salt, rainbow-table vulneravel. Werkzeug (ja instalado com
             Flask) oferece generate_password_hash seguro.
Impact: Todas as senhas sao trivialmente reversiveis; autenticacao comprometida.
Recommendation: Substituir por werkzeug.security (Playbook #2).

[CRITICAL] Sensitive Data Exposure
File: models/user.py:21
Description: to_dict() inclui 'password': self.password, vazando o hash em TODAS as
             respostas: GET /users, GET /users/<id>, POST /users, POST /login
             (user_routes.py:33-40,85-86,129,209).
Impact: Exposicao do hash de senha a qualquer cliente; facilita cracking offline.
Recommendation: Remover 'password' do to_dict (Playbook #3).

[HIGH] Debug Mode RCE
File: app.py:34
Description: app.run(debug=True, host='0.0.0.0', port=5000) expoe o debugger
             interativo do Werkzeug em todas as interfaces de rede.
Impact: Execucao remota de codigo (RCE) por qualquer cliente que alcance a porta.
Recommendation: debug via env (default False) + bind em 127.0.0.1 (Playbook #5).

[HIGH] Missing AuthN/AuthZ
File: routes/user_routes.py:210
Description: /login retorna 'token': 'fake-jwt-token-' + str(user.id) — string
             previsivel e nao assinada. Nenhum middleware consome o token; todas as
             rotas (incluindo DELETE /tasks, PUT) sao acessiveis sem credencial.
Impact: Qualquer cliente forja um token adivinhando o user id; bypass total de auth.
Recommendation: Emitir JWT real assinado + middleware verifyToken (Playbook #7).

[HIGH] N+1 / Queries in Loops
File: routes/task_routes.py:42,51
Description: GET /tasks faz, para cada task, User.query.get(t.user_id) e
             Category.query.get(t.category_id) — 1+2N queries. As relacoes user/category
             ja existem no modelo (task.py:20-21) mas nao sao usadas (joinedload).
Impact: Degradacao linear de performance com o numero de tasks.
Recommendation: Usar joinedload/selectinload ou JOIN (Playbook #9).

[HIGH] Business Logic in Routes
File: routes/task_routes.py:85-154 (create); routes/task_routes.py:156-223 (update)
Description: ~70 linhas de validacao (title length, status, priority, FK, parse de data)
             e mutacao ORM inline no handler HTTP. A pasta services/ existe mas seus
             modulos nunca sao importados — a separacao e cosmética.
Impact: Rotas pesadas e nao testaveis; validacao duplicada 3x (model, helpers, routes).
Recommendation: Extrair validacao para schemas e orchestr para services (Playbook #8).

[MEDIUM] Deprecated API Usage
File: routes/task_routes.py:67,117,158,188,195,227; routes/user_routes.py (multiplos)
Description: Model.query.get(pk) e a API legacy do SQLAlchemy 1.x; em 2.x o idiomático
             e db.session.get(Model, pk). Usado 15+ vezes no codigo todo.
Impact: Codigo fora do padrao atual; quebra em upgrade maior do SQLAlchemy.
Recommendation: Migrar para db.session.get() (Playbook #11).

[MEDIUM] No Centralized Error Handling
File: routes/task_routes.py:62,137,204,236; routes/user_routes.py:130,149
Description: except: bare (sem tipo) engole KeyboardInterrupt/SystemExit e esconde
             erros de programacao. Nao ha @app.errorhandler registrado em app.py.
Impact: Erros silenciados, 500 genericos, sem observabilidade.
Recommendation: Registrar errorhandler central + except tipado (Playbook #10).

[MEDIUM] Dead Code / Unused Dependencies
File: services/notification_service.py (todo); utils/helpers.py; requirements.txt:4-6
Description: NotificationService nunca e instanciado em lugar nenhum. helpers.py
             (validate_email, sanitize_string, process_task_data) nunca chamados.
             marshmallow, requests, python-dotenv declarados mas nunca importados.
Impact: Superficie de dependencia inflada (risco de supply-chain); codigo confuso.
Recommendation: Remover mortos ou conectar de fato (Playbook #12).

[LOW] Magic Numbers/Strings + DRY
File: routes/task_routes.py:110,177 (status list); routes/task_routes.py:30-39,71-80 (overdue)
Description: Lista de status validos hardcoded em 3+ locais (existem em helpers.py:110 mas
             nunca importados). Logica "overdue" duplicada em 5+ lugares enquanto
             Task.is_overdue() (task.py:50) nunca e chamado.
Impact: Mudancas exigem edicao em multiplos pontos; risco de inconsistencia.
Recommendation: Extrair constants/Enum e usar Task.is_overdue() (Playbook #12).

[LOW] Import-time Side Effects
File: app.py:30-31
Description: db.create_all() roda como side-effect de importar app (dentro de
             app_context no nivel do modulo), nao em uma factory create_app(). Importar
             app (em testes/seed) muta o filesystem.
Impact: Acoplamento startup-DB; dificulta testes isolados.
Recommendation: Adotar create_app() factory (Playbook #5).

================================
Total: 12 findings (3 CRITICAL, 4 HIGH, 3 MEDIUM, 2 LOW)
================================
