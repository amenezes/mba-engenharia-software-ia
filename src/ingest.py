import os

import click
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter


@click.command()
@click.option(
    "--pdf",
    envvar="PDF_PATH",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Caminho do PDF a ingerir.",
)
@click.option("--db-url", envvar="DATABASE_URL", required=True, help="URL do PostgreSQL (pgVector).")
@click.option("--collection", envvar="COLLECTION_NAME", default="pdf_docs", show_default=True, help="Nome da colecao no banco.")
@click.option("--chunk-size", envvar="CHUNK_SIZE", default=1000, type=int, show_default=True, help="Tamanho do chunk em caracteres.")
@click.option("--chunk-overlap", envvar="CHUNK_OVERLAP", default=150, type=int, show_default=True, help="Overlap entre chunks em caracteres.")
@click.option("--embedding-model", envvar="EMBEDDING_MODEL", default="text-embedding-3-small", show_default=True, help="Modelo de embedding OpenAI.")
@click.option("--api-base", envvar="OPENAI_API_BASE", default="https://api.openai.com/v1", show_default=True, help="Base URL do provedor OpenAI-compativel.")
@click.option("--api-key", envvar="OPENAI_API_KEY", required=True, help="Chave de API do provedor.")
def main(pdf, db_url, collection, chunk_size, chunk_overlap, embedding_model, api_base, api_key):
    """Ingestao de PDF no banco vetorial (PostgreSQL + pgVector)."""
    click.echo(f"Carregando PDF: {pdf}")
    documentos = PyPDFLoader(pdf).load()
    click.echo(f"  paginas carregadas: {len(documentos)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(documentos)
    click.echo(f"  chunks gerados: {len(chunks)} (size={chunk_size}, overlap={chunk_overlap})")

    embeddings = OpenAIEmbeddings(
        model=embedding_model,
        base_url=api_base,
        api_key=api_key,
    )
    click.echo(f"Conectando ao banco e resetando a colecao '{collection}'...")
    store = PGVector(
        embeddings=embeddings,
        connection=db_url,
        collection_name=collection,
        pre_delete_collection=True,
        use_jsonb=True,
    )
    store.add_documents(chunks)

    click.echo(f"Ingestao concluida: {len(chunks)} chunks armazenados em '{collection}'.")


if __name__ == "__main__":
    load_dotenv()
    main()
