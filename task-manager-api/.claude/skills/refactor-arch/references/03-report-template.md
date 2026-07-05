# 03 — Template de Relatorio de Auditoria

Modelo padronizado para a **Fase 2**. O relatorio DEVE seguir este formato exato,
com os findings ordenados por severidade (CRITICAL → HIGH → MEDIUM → LOW) e cada
um contendo `File`, `Description`, `Impact` e `Recommendation`.

## Template

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome-do-projeto>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<LOC> lines of code

Summary
CRITICAL: <c> | HIGH: <h> | MEDIUM: <m> | LOW: <l>

Findings

[CRITICAL] <Titulo do Anti-Pattern>
File: <caminho>:<linha-inicio>-<linha-fim>
Description: <o que foi encontrado, contextualizado>
Impact: <por que importa / consequencia>
Recommendation: <acao de correcao — referencia ao playbook>

[HIGH] <Titulo>
File: <caminho>:<linha>
Description: ...
Impact: ...
Recommendation: ...

[MEDIUM] <Titulo>
File: <caminho>:<linha>
Description: ...
Impact: ...
Recommendation: ...

[LOW] <Titulo>
File: <caminho>:<linha>
Description: ...
Impact: ...
Recommendation: ...

================================
Total: <N> findings
================================
```

## Regras de preenchimento

1. **Ordem obrigatoria**: CRITICAL primeiro, depois HIGH, MEDIUM, LOW.
2. **File deve ser exato**: `<caminho-relativo>:<linha>` ou `<linha-inicio>-<linha-fim>`
   para blocos. Use `app.py:7` ou `models.py:289-297`.
3. **Description**: descreva o QUE foi encontrado (nao o anti-pattern generico).
   Cite o valor/variavel real. Ex: `"SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'"`.
4. **Impact**: consequencia concreta. Ex: `"permite falsificacao de sessao"`,
   `"RCE remoto via debugger Werkzeug"`.
5. **Recommendation**: acao + referencia ao playbook. Ex: `"Mover para
   `os.environ['SECRET_KEY']` (Playbook #1)"`.
6. **Nao inclua findings duplicados** para o mesmo problema — agrupe se aplicavel.
7. **Minimo de 5 findings** por projeto (criterio de aceite).

## Exemplo completo

```markdown
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
             no codigo, sem leitura de variavel de ambiente.
Impact: Permite falsificacao de sessoes Flask por qualquer pessoa com acesso ao
        codigo-fonte.
Recommendation: Mover para os.environ['SECRET_KEY'] com fallback em .env (Playbook #1).

[CRITICAL] SQL Injection
File: models.py:289-297
Description: Funcao buscar_produtos concatena termos de busca (termo, categoria,
             preco_min, preco_max) diretamente na string SQL via f-string.
Impact: Endpoint de busca exploravel para injecao SQL — exfiltracao e DROP.
Recommendation: Parametrizar com placeholders '?' (Playbook #4).

[CRITICAL] God Class / God Method
File: models.py:1-314
Description: Arquivo unico de 314 linhas contem toda logica de negocio, queries SQL,
             validacao e formatacao para 4 dominios (produtos, usuarios, pedidos, itens).
Impact: Impossivel testar em isolamento; qualquer mudanca afeta todos os dominios.
Recommendation: Separar em models e controllers por dominio (Playbook #6).

[CRITICAL] Debug Mode RCE
File: app.py:8,88
Description: app.run(debug=True, host='0.0.0.0') expoe o debugger interativo do
             Werkzeug em todas as interfaces de rede.
Impact: Execucao remota de codigo (RCE) por qualquer cliente que alcance a porta 5000.
Recommendation: debug via env (default False) + bind em localhost (Playbook #5).

[CRITICAL] Sensitive Data Exposure
File: models.py:83,99 (senha em to_dict); controllers.py:287-289 (/health)
Description: get_todos_usuarios e get_usuario_por_id incluem a coluna 'senha' nos
             dicts serializados, vazando para GET /usuarios e GET /usuarios/<id>.
Impact: Qualquer cliente anonimo recebe as senhas (em texto plano) de todos os usuarios.
Recommendation: Remover 'senha' do to_dict (Playbook #3).

[HIGH] N+1 Queries
File: models.py:171-233
Description: Listagem de pedidos abre, para cada pedido, um cursor para itens e, para
             cada item, outro cursor para produto — padrao 1+N+N*M queries.
Impact: Degradacao quadratica de performance; 100 pedidos x 5 itens = 601 queries.
Recommendation: Substituir por JOIN unico ou joinedload (Playbook #9).

[HIGH] Missing AuthN/AuthZ
File: app.py:47-78
Description: Endpoints /admin/reset-db e /admin/query nao possuem qualquer decorator
             ou middleware de autenticacao/autorizacao.
Impact: Qualquer cliente anonimo pode resetar o banco ou executar SQL arbitrario.
Recommendation: Adicionar camada de auth + RBAC (Playbook #7).

[HIGH] Business Logic in Controllers
File: controllers.py:208-210,247-250 (notificacoes); models.py:256-262 (desconto)
Description: Notificacoes (EMAIL/SMS/PUSH) sao print() inline no controller de
             criar_pedido; a regra de desconto vive dentro do "model" relatorio_vendas.
Impact: Regras de negocio acopladas ao transporte HTTP; impossivel testar isoladamente.
Recommendation: Extrair para services (notificacao_service, relatorio_service) (Playbook #8).

[MEDIUM] No Centralized Error Handling
File: controllers.py:12,22,62,96
Description: Controllers capturam Exception genericamente e retornam str(e) ao cliente,
             sem errorhandler central registrado no app.
Impact: Vazamento de stack trace, comportamento inconsistente entre endpoints.
Recommendation: Registrar @app.errorhandler e logar estruturadamente (Playbook #10).

[MEDIUM] Deprecated API Usage
File: models.py (múltiplos locais)
Description: Uso de padrao de driver sqlite3 cru com check_same_thread=False em servidor
             multi-thread; ausencia de ORM/repository abstrato.
Impact: Race conditions, queries espalhadas, dificuldade de evolucao do schema.
Recommendation: Adotar repository pattern ou ORM (Playbook #11).

[LOW] Magic Numbers/Strings
File: models.py:256-262
Description: Regra de desconto hardcoded com magic numbers (10000, 0.1, 5000, 0.05,
             1000, 0.02) sem constantes nomeadas.
Impact: Regra de negocio opaca; mudanca exige cacada pelos literais.
Recommendation: Extrair para constantes/Enum (Playbook #12).

[LOW] Poor Naming / Shadowing
File: models.py:187,219 (cursor2, cursor3); models.py:24 (id)
Description: Variaveis cursor2/cursor3 mascaram o smell N+1; parametro 'id' sombreia
             o builtin Python.
Impact: Legibilidade e manutenibilidade reduzidas.
Recommendation: Renomear e usar nomes descritivos (Playbook #12).

================================
Total: 12 findings
================================
```

## Saida para o humano (console)

Apos salvar em `reports/audit-project-<N>.md`, imprima o relatorio no console e
entao faca a pausa obrigatoria:

```
================================
Total: <N> findings (<C> CRITICAL, <H> HIGH, <M> MEDIUM, <L> LOW)
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
>
```
