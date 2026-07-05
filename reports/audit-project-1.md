================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

Summary
CRITICAL: 5 | HIGH: 3 | MEDIUM: 2 | LOW: 2

Findings

[CRITICAL] Hardcoded Secrets
File: app.py:7
Description: SECRET_KEY definida como 'minha-chave-super-secreta-123' diretamente
             no codigo, sem leitura de variavel de ambiente. Tambem em
             controllers.py:289 o /health expoe essa chave na resposta JSON.
Impact: Permite falsificacao de sessoes Flask por qualquer pessoa com acesso ao
        codigo-fonte ou ao endpoint /health; compromete assinaturas CSRF.
Recommendation: Mover para os.environ['SECRET_KEY'] com .env (Playbook #1).

[CRITICAL] SQL Injection
File: models.py:28,48-49,58-60,68,92,109-110,127-128,140,150,158-160,164-165,174,188,192,220,224,280,289-297
Description: Quase toda query monta SQL por concatenacao de strings ("SELECT ... " + str(id))
             ou f-strings, sem placeholders parametrizados. O caso mais critico e
             buscar_produtos (models.py:289-297) que injeta termo/categoria/preco
             direto no WHERE, e login_usuario (models.py:109-110) que concatena
             email e senha. Note que database.py:70-73 ja usa '?' corretamente.
Impact: Bypass de autenticacao via login, exfiltracao de dados e DROP/ALTER
        arbitrario; o endpoint /admin/query (app.py:59-78) ainda executa SQL cru.
Recommendation: Parametrizar todas as queries com placeholders '?' (Playbook #4).

[CRITICAL] Sensitive Data Exposure
File: models.py:83,99 (senha em to_dict); controllers.py:287-289 (/health)
Description: get_todos_usuarios e get_usuario_por_id incluem a coluna 'senha' nos
             dicts serializados, vazando para GET /usuarios e GET /usuarios/<id>.
             O endpoint /health retorna db_path, debug=True e o proprio secret_key.
Impact: Qualquer cliente anonimo recebe as senhas (em texto plano) de todos os
        usuarios; vazamento de configuracao interna.
Recommendation: Remover 'senha' do to_dict e dados sensiveis do /health (Playbook #3).

[CRITICAL] God Class / God Method
File: models.py:1-314
Description: Arquivo unico de 314 linhas concentra queries SQL, regras de negocio
             (descontos em relatorio_vendas:256-262), validacao de estoque e
             formatacao para 4 dominios (produtos, usuarios, pedidos, itens_pedido).
Impact: Impossivel testar em isolamento; qualquer mudanca em um dominio afeta
        todos os outros; viola Single Responsibility.
Recommendation: Separar em models e controllers por dominio (Playbook #6).

[CRITICAL] Debug Mode RCE
File: app.py:8,88
Description: app.config['DEBUG'] = True e app.run(host='0.0.0.0', port=5000, debug=True)
             expoe o debugger interativo do Werkzeug em todas as interfaces de rede.
Impact: Execucao remota de codigo (RCE) por qualquer cliente que alcance a porta
        5000 — o debugger permite rodar Python arbitrario no servidor.
Recommendation: debug via env (default False) + bind em 127.0.0.1 (Playbook #5).

[HIGH] Missing AuthN/AuthZ
File: app.py:47-78 (admin endpoints); controllers.py:176-180 (login sem token)
Description: /admin/reset-db e /admin/query nao possuem qualquer decorator ou
             middleware de autenticacao. O endpoint /login valida a senha mas nao
             emite token (JWT/sessao); nenhuma rota e protegida.
Impact: Qualquer cliente anonimo pode resetar o banco, executar SQL arbitrario,
        listar usuarios e pedidos, alterar status.
Recommendation: Adicionar camada de auth + JWT real + RBAC (Playbook #7).

[HIGH] N+1 / Queries in Loops
File: models.py:171-233 (listagem de pedidos); models.py:139-166 (criar_pedido)
Description: Para cada pedido, abre-se cursor para itens_pedido e, para cada item,
             outro cursor para produtos — padrao 1+N+N*M. Em criar_pedido ha dois
             loops com queries de validacao e depois de insercao, sem transacao.
Impact: Degradacao quadratica: 100 pedidos x 5 itens = 601 queries; risco de
        overselling por ausencia de lock/transaction no decremento de estoque.
Recommendation: Substituir por JOIN unico ou joinedload; envolver em transacao (Playbook #9).

[HIGH] Business Logic in Controllers
File: controllers.py:208-210,247-250 (notificacoes); models.py:256-262 (desconto)
Description: Notificacoes (EMAIL/SMS/PUSH) sao print() inline no controller de
             criar_pedido e atualizar_status_pedido. A regra de desconto por faixa
             de faturamento vive dentro do "model" relatorio_vendas.
Impact: Regras de negocio acopladas ao transporte HTTP; impossivel testar
        isoladamente; mudancas exigem edicao em multiplos pontos.
Recommendation: Extrair para services (notificacao_service, relatorio_service) (Playbook #8).

[MEDIUM] No Centralized Error Handling
File: controllers.py:10-12,22,60-62,95-96,108-109,125-126,133-134,143-144,164-165,185-186,218-220,226-227,234-235,254-255,261-262,291-292
Description: Todos os controllers capturam Exception genericamente e retornam
             str(e) ao cliente; nao ha @app.errorhandler registrado no app.
             models.py nao tem nenhum tratamento de erro.
Impact: Vazamento de stack trace/erros internos ao cliente; comportamento
        inconsistente entre endpoints; sem observabilidade.
Recommendation: Registrar @app.errorhandler central + logar estruturadamente (Playbook #10).

[MEDIUM] Magic Numbers/Strings + DRY
File: models.py:256-262 (10000, 0.1, 5000, 0.05, 1000, 0.02); controllers.py:47-50,52; models.py:171-201 vs 203-233
Description: Faixas de desconto hardcoded sem constantes nomeadas; limites de
             nome (2, 200) e lista de categorias validas inline. As funcoes
             get_pedidos_usuario e get_todos_pedidos sao ~90% identicas (mudam so
             o WHERE).
Impact: Regras de negocio opacas e espalhadas; correcoes precisam ser aplicadas
        em duplicata.
Recommendation: Extrair constantes/Enum e unificar funcoes duplicadas (Playbook #12).

[LOW] Inconsistent Routing / No Blueprints
File: app.py:11-30 (add_url_rule) vs app.py:32,47,59 (@app.route)
Description: Dois estilos de registro de rota coexistem sem motivo; o app e flat
             (sem Blueprints), impedindo modularizacao por dominio.
Impact: Organizacao pobre; dificil dividir em modulos ou versionar a API.
Recommendation: Adotar Blueprints por dominio (Playbook #6).

[LOW] Poor Naming / Builtin Shadowing
File: models.py:187,191,219,223 (cursor2, cursor3); models.py:24,89 (parametro id)
Description: Variaveis cursor2/cursor3 mascaram o smell N+1; o parametro 'id'
             sombreia o builtin Python em varias funcoes.
Impact: Legibilidade reduzida e manutibilidade comprometida.
Recommendation: Renomear para nomes descritivos (Playbook #12).

================================
Total: 12 findings (5 CRITICAL, 3 HIGH, 2 MEDIUM, 2 LOW)
================================
