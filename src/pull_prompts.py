"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPT_HUB_NAME = "leonanluppi/bug_to_user_story_v1"
OUTPUT_PATH = "prompts/bug_to_user_story_v1.yml"


def extract_messages(prompt_template: ChatPromptTemplate) -> dict:
    """Extrai system_prompt e user_prompt de um ChatPromptTemplate."""
    system_prompt = ""
    user_prompt = ""

    for message in prompt_template.messages:
        if isinstance(message, SystemMessagePromptTemplate):
            system_prompt = message.prompt.template
        elif isinstance(message, HumanMessagePromptTemplate):
            user_prompt = message.prompt.template

    return {"system_prompt": system_prompt, "user_prompt": user_prompt}


def pull_prompts_from_langsmith():
    print(f"   Fazendo pull do prompt: {PROMPT_HUB_NAME}")

    prompt_template = hub.pull(PROMPT_HUB_NAME)
    print(f"   ✓ Prompt carregado do LangSmith Hub")

    messages = extract_messages(prompt_template)

    prompt_data = {
        "bug_to_user_story_v1": {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": messages["system_prompt"],
            "user_prompt": messages["user_prompt"],
            "version": "v1",
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    success = save_yaml(prompt_data, OUTPUT_PATH)
    if success:
        print(f"   ✓ Prompt salvo em: {OUTPUT_PATH}")
        return True
    else:
        print(f"   ❌ Erro ao salvar prompt em: {OUTPUT_PATH}")
        return False


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH")

    required_vars = ["LANGSMITH_API_KEY"]
    if not check_env_vars(required_vars):
        return 1

    success = pull_prompts_from_langsmith()

    if success:
        print("\n✅ Pull concluído com sucesso!")
        print(f"   Arquivo: {OUTPUT_PATH}")
        return 0
    else:
        print("\n❌ Falha ao fazer pull do prompt.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
