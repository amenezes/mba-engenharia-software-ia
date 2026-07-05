================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.18.2
Files:   3 analyzed | ~180 lines of code (app.js=14, AppManager.js=141, utils.js=25)

Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 3 | LOW: 2

Findings

[CRITICAL] Hardcoded Secrets
File: src/utils.js:2-5
Description: Senha de DB ('senha_super_secreta_prod_123'), chave de pagamento Stripe
             LIVE ('pk_live_1234567890abcdef') e credenciais SMTP commitadas em texto
             plano no objeto config. Sem .env / dotenv / .gitignore.
Impact: Qualquer leak do repo compromete pagamentos reais e acesso ao banco; sem
        rotacao possivel sem editar codigo.
Recommendation: Mover para process.env via dotenv + .env.example (Playbook #1).

[CRITICAL] Insecure Password Storage
File: src/utils.js:17-23
Description: Funcao badCrypto "hasheia" a senha concatenando Base64 em loop 10000x e
             truncando para 10 chars. Base64 e codificacao (reversivel), nao cripto;
             sem salt, colisoes massivas, rainbow-table vulneravel. Senha default
             "123456" aceita quando ausente (AppManager.js:68).
Impact: Todas as senhas sao trivialmente reversiveis; autenticacao quebrada.
Recommendation: Substituir por bcrypt/argon2 (Playbook #2).

[CRITICAL] Sensitive Data Exposure
File: src/AppManager.js:45
Description: console.log imprime o numero do cartao (PAN) cru e a chave do gateway
             de pagamento em cada checkout. Log andCache (utils.js:13) tambem loga.
Impact: Violacao direta do PCI-DSS Requirement 3; logs geralmente sao agregados e
        multiplicam a exposicao do PAN.
Recommendation: Remover logs de PAN/secrets; redacting logger (Playbook #3).

[CRITICAL] God Class
File: src/AppManager.js:4-141
Description: A classe AppManager detem a conexao DB (:7), o bootstrap de schema +
             seeds (initDb:10-23) e TODAS as rotas com logica inline (setupRoutes:25-138).
             O metodo setupRoutes tem ~114 linhas com SQL, pagamento, auditoria e
             criacao de usuario embutidos nos handlers.
Impact: Single Responsibility violado; incontrolavel e impossivel de testar
        isoladamente; qualquer mudanca e de alto risco.
Recommendation: Decompor em models + controllers + services + routes (Playbook #6).

[HIGH] Missing AuthN/AuthZ
File: src/AppManager.js:80 (financial-report); src/AppManager.js:131 (DELETE user)
Description: /api/admin/financial-report expoe receita e PII de estudantes sem
             qualquer auth; DELETE /api/users/:id permite que qualquer cliente anonimo
             delete usuarios. Nao ha JWT/sessao/API-key em lugar nenhum.
Impact: Escalonamento vertical/horizontal; destruicao de dados e exfiltracao
        financeira por qualquer cliente.
Recommendation: Adicionar middleware JWT + RBAC (Playbook #7).

[HIGH] N+1 / Queries in Loops
File: src/AppManager.js:83-127
Description: O relatorio financeiro faz 1 query de courses, +1 por course para
             enrollments, +2 por enrollment (users + payments) — padrao quadratico
             1+C+E+2E. Tudo em callbacks aninhadas com contadores manuais.
Impact: Degradacao cubica de performance; contadores frageis podem deixar a
        requisicao pendente se um callback errar (err ignorado em :92,:104,:106).
Recommendation: Substituir por um unico SELECT com JOIN (Playbook #9).

[HIGH] Business Logic in Routes
File: src/AppManager.js:43-64 (pagamento); src/AppManager.js:46 (fake gateway)
Description: A logica de pagamento — status = cc.startsWith("4") ? "PAID" : "DENIED" —
             vive inline no handler HTTP, junto com inserts de enrollment/payment/audit.
             Qualquer string comecando com "4" aprova pagamento.
Impact: Regra de negocio critique (pagamento) acoplada ao transporte; fake gateway
        trivialmente burlavel; sem idempotencia.
Recommendation: Extrair para paymentService + checkoutService (Playbook #8).

[MEDIUM] No Centralized Error Handling
File: src/app.js (sem error middleware); src/AppManager.js:133-135
Description: Nao existe middleware (err, req, res, next) no app Express. O handler
             DELETE ignora o parametro err (AppManager.js:133) e sempre responde sucesso.
             Erros internos viram stack trace cru.
Impact: Comportamento inconsistente, erros silenciados, vazamento de detalhes.
Recommendation: Registrar errorHandler central + logs estruturados (Playbook #10).

[MEDIUM] Deprecated API Usage
File: src/AppManager.js:1 (sqlite3.verbose()); src/app.js:6 (express.json sem limit)
Description: API callback-style do sqlite3 obriga o callback hell; .verbose() loga
             todo SQL em producao. Nao ha helmet, cors, rate-limiting. Express 4.18
             sem padroes modernos (async middleware, ESM).
Impact: Codigo fragil, ruidoso, fora do idiomatico atual; dificil migrar.
Recommendation: Migrar para sqlite Promise-based + helmet + ESM (Playbook #11).

[MEDIUM] Magic Numbers/Strings
File: src/utils.js:19,22 (10000, 10); src/AppManager.js:46,108 ("4","PAID","DENIED")
Description: Literais magicos espalhados: 10000 iteracoes, trunc 10 chars, prefixo
             "4" do BIN, status "PAID"/"DENIED" repetidos em 4+ locais sem enum/const.
Impact: Regras opacas; um typo ("PIAD") quebraria silenciosamente o calculo de receita.
Recommendation: Extrair PAYMENT_STATUS enum + constantes (Playbook #12).

[LOW] Global Mutable State
File: src/utils.js:9-10
Description: globalCache cresce indefinidamente (sem TTL/eviccao — vazamento de
             memoria); totalRevenue e exportado mas nunca escrito (dead code).
Impact: Vazamento de memoria e risco de bleed entre requisicoes/tenants.
Recommendation: Remover ou mover para cache externo (Redis) com TTL (Playbook #12).

[LOW] Poor Naming
File: src/AppManager.js:26,29-33
Description: Variaveis de uma letra (u, e, p) e abreviacoes (cc, cid, enr); chaves
             de body ofuscadas (usr, eml, c_id); const self = this (pre-arrow-function).
Impact: Legibilidade e buscabilidade reduzidas.
Recommendation: Renomear para nomes descritivos; usar arrow functions (Playbook #12).

================================
Total: 12 findings (4 CRITICAL, 3 HIGH, 3 MEDIUM, 2 LOW)
================================
