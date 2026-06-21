# Ingestão e Busca Semântica com LangChain e Postgres

## Como executar

### Pré-requisitos

- Python 3.12+
- Docker e Docker Compose

### 1. Ambiente virtual e dependências

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuração (.env)

```bash
cp .env.example .env
```

Edite o `.env` e preencha a `OPENAI_API_KEY`. As demais variáveis já vêm com defaults utilizáveis (`DATABASE_URL`, modelos, chunks, etc.).

### 3. Banco de dados (PostgreSQL + pgVector)

```bash
docker compose up -d
```

Sobe um container `pgvector/pgvector:pg16` na porta `5432` com a extensão `vector` já habilitada (via `init.sql`).

### 4. Ingestão do PDF

```bash
python src/ingest.py
```

Por padrão lê o arquivo definido em `PDF_PATH` (`document.pdf`). O PDF é dividido em chunks de 1000 caracteres (overlap 150), convertido em embeddings e armazenado no pgVector. A coleção é recriada a cada execução (idempotente).

Para ingerir outro arquivo:

```bash
python src/ingest.py --pdf outro.pdf
```

### 5. Chat (pergunta e resposta)

```bash
python src/chat.py "Qual sua pergunta?"
```

Retorna a resposta com base apenas no conteúdo do PDF. Perguntas fora do contexto recebem:

> "Não tenho informações necessárias para responder sua pergunta."

### 6. Busca semântica (ferramenta auxiliar)

Para inspecionar os chunks recuperados sem chamar o LLM:

```bash
python src/search.py "Qual sua pergunta?"              # só o resumo (default: sem contexto)
python src/search.py "Qual sua pergunta?" --contexto   # exibe cada chunk: [n] page=X / conteúdo / ---
```

## Usando OpenRouter (provedor OpenAI-compatível)

Por padrão o projeto usa a OpenAI direta. Para usar o [OpenRouter](https://openrouter.ai/) (útil onde o acesso direto à OpenAI é restrito), ajuste o `.env`:

```env
OPENAI_API_KEY=sk-or-v1-...
OPENAI_API_BASE=https://openrouter.ai/api/v1
EMBEDDING_MODEL=openai/text-embedding-3-small
LLM_MODEL=openai/gpt-4o-mini
```

Note o prefixo `openai/` nos nomes dos modelos — obrigatório no OpenRouter.


