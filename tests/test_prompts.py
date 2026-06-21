"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_V2_PATH = str(Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml")


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class TestPrompts:
    @pytest.fixture
    def prompt_data(self):
        """Carrega os dados do prompt v2."""
        data = load_prompts(PROMPT_V2_PATH)
        return data["bug_to_user_story_v2"]

    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data
        assert prompt_data["system_prompt"].strip() != ""

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: 'Você é um Product Manager')."""
        system_prompt = prompt_data["system_prompt"].lower()
        assert "você é um" in system_prompt or "você é uma" in system_prompt

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt_data["system_prompt"].lower()
        assert "markdown" in system_prompt or "user story" in system_prompt

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        assert "few_shot_examples" in prompt_data
        assert len(prompt_data["few_shot_examples"]) >= 2

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        full_text = str(prompt_data)
        assert "[TODO]" not in full_text
        assert "TODO" not in prompt_data.get("system_prompt", "")

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        assert "techniques_applied" in prompt_data
        assert len(prompt_data["techniques_applied"]) >= 2

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])