import click
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector


def buscar(pergunta, k, db_url, collection, embedding_model, api_base, api_key):
    """Recupera os k chunks mais similares a `pergunta` no banco vetorial."""
    embeddings = OpenAIEmbeddings(
        model=embedding_model,
        base_url=api_base,
        api_key=api_key,
    )
    store = PGVector(
        embeddings=embeddings,
        connection=db_url,
        collection_name=collection,
        create_extension=False,
    )
    return store.similarity_search(pergunta, k=k)


def formatar_contexto(docs):
    """Concatena o conteudo dos chunks separados por divisor."""
    return "\n\n---\n\n".join(d.page_content for d in docs)


@click.command()
@click.argument("pergunta")
@click.option("--k", envvar="SEARCH_K", default=10, type=int, show_default=True, help="Numero de chunks recuperados.")
@click.option("--db-url", envvar="DATABASE_URL", required=True, help="URL do PostgreSQL (pgVector).")
@click.option("--collection", envvar="COLLECTION_NAME", default="pdf_docs", show_default=True, help="Nome da colecao no banco.")
@click.option("--embedding-model", envvar="EMBEDDING_MODEL", default="text-embedding-3-small", show_default=True, help="Modelo de embedding OpenAI.")
@click.option("--api-base", envvar="OPENAI_API_BASE", default="https://api.openai.com/v1", show_default=True, help="Base URL do provedor OpenAI-compativel.")
@click.option("--api-key", envvar="OPENAI_API_KEY", required=True, help="Chave de API do provedor.")
@click.option("--contexto/--sem-contexto", default=False, show_default=True, help="Exibe o conteudo de cada chunk recuperado.")
def main(pergunta, k, db_url, collection, embedding_model, api_base, api_key, contexto):
    """Busca semantica no banco vetorial (PostgreSQL + pgVector)."""
    click.echo(f"Buscando: {pergunta!r} (k={k})")
    docs = buscar(pergunta, k, db_url, collection, embedding_model, api_base, api_key)
    click.echo(f"chunks recuperados: {len(docs)}")
    if contexto:
        for i, d in enumerate(docs, 1):
            click.echo(f"[{i}] page={d.metadata.get('page')}")
            click.echo(d.page_content)
            click.echo("---")


if __name__ == "__main__":
    load_dotenv()
    main()
