"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPT_FILE = "prompts/bug_to_user_story_v2.yml"
PROMPT_NAME = "bug_to_user_story_v2"


def extract_inner_dict(prompt_data: dict) -> dict:
    """Extrai o dict interno caso o YAML tenha estrutura aninhada."""
    if len(prompt_data) == 1 and isinstance(list(prompt_data.values())[0], dict):
        inner_key = list(prompt_data.keys())[0]
        return prompt_data[inner_key]
    return prompt_data


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt (ex: bug_to_user_story_v2)
        prompt_data: Dados do prompt (pode ser aninhado ou plano)

    Returns:
        True se sucesso, False caso contrário
    """
    inner = extract_inner_dict(prompt_data)

    username = os.getenv("USERNAME_LANGSMITH_HUB", "")
    if not username:
        print("   ❌ USERNAME_LANGSMITH_HUB não configurado")
        return False

    repo_full_name = f"{username}/{prompt_name}"

    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", inner["system_prompt"]),
        ("human", inner["user_prompt"]),
    ])

    tags = inner.get("tags", []) + inner.get("techniques_applied", [])
    description = inner.get("description", "")

    print(f"   Fazendo push para: {repo_full_name}")

    try:
        hub.push(
            repo_full_name=repo_full_name,
            object=chat_prompt,
            new_repo_is_public=True,
            new_repo_description=description,
            tags=tags,
        )
    except Exception as e:
        if "409" in str(e) or "Nothing to commit" in str(e):
            print(f"   ✓ Prompt já está atualizado (sem alterações desde último commit)")
        else:
            raise

    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt (pode ser aninhado ou plano)

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    inner = extract_inner_dict(prompt_data)
    return validate_prompt_structure(inner)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS")

    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if not check_env_vars(required_vars):
        return 1

    prompt_data = load_yaml(PROMPT_FILE)
    if prompt_data is None:
        print(f"❌ Não foi possível carregar: {PROMPT_FILE}")
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Validação falhou:")
        for error in errors:
            print(f"   - {error}")
        return 1

    print("   ✓ Validação passou")

    techniques = extract_inner_dict(prompt_data).get("techniques_applied", [])
    print(f"   ✓ Técnicas aplicadas: {', '.join(techniques)}")

    try:
        success = push_prompt_to_langsmith(PROMPT_NAME, prompt_data)
        if success:
            username = os.getenv("USERNAME_LANGSMITH_HUB")
            print(f"   ✓ Push concluído: {username}/{PROMPT_NAME}")
            print(f"\n✅ Push realizado com sucesso!")
            print(f"   Dashboard: https://smith.langchain.com/prompts")
            return 0
        else:
            print(f"\n❌ Falha no push.")
            return 1
    except Exception as e:
        print(f"\n❌ Erro no push: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
