import click
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from search import buscar, formatar_contexto


PROMPT_TEMPLATE = """CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO\""""


@click.command()
@click.argument("pergunta")
@click.option("--k", envvar="SEARCH_K", default=10, type=int, show_default=True, help="Numero de chunks recuperados por pergunta.")
@click.option("--llm-model", envvar="LLM_MODEL", default="gpt-4o-mini", show_default=True, help="Modelo LLM usado nas respostas.")
@click.option("--db-url", envvar="DATABASE_URL", required=True, help="URL do PostgreSQL (pgVector).")
@click.option("--collection", envvar="COLLECTION_NAME", default="pdf_docs", show_default=True, help="Nome da colecao no banco.")
@click.option("--embedding-model", envvar="EMBEDDING_MODEL", default="text-embedding-3-small", show_default=True, help="Modelo de embedding OpenAI.")
@click.option("--api-base", envvar="OPENAI_API_BASE", default="https://api.openai.com/v1", show_default=True, help="Base URL do provedor OpenAI-compativel.")
@click.option("--api-key", envvar="OPENAI_API_KEY", required=True, help="Chave de API do provedor.")
def main(pergunta, k, llm_model, db_url, collection, embedding_model, api_base, api_key):
    """Responde uma pergunta com base no PDF ingerido (PostgreSQL + pgVector + LLM)."""
    llm = ChatOpenAI(model=llm_model, base_url=api_base, api_key=api_key)
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | llm | StrOutputParser()

    docs = buscar(pergunta, k, db_url, collection, embedding_model, api_base, api_key)
    contexto = formatar_contexto(docs)
    resposta = chain.invoke({"contexto": contexto, "pergunta": pergunta})
    click.echo(f"RESPOSTA: {resposta}")


if __name__ == "__main__":
    load_dotenv()
    main()
