"""
Wrapper para executar evaluate.py respeitando o rate limit do Gemini free tier.

Adiciona um delay entre chamadas e aumenta max_retries para permitir
que o mecanismo de retry espere o reset da quota (janela de 1 minuto).

Não modifica nenhum arquivo original (evaluate.py, utils.py, metrics.py).

Uso: python run_eval.py
"""
import time
import functools
from dotenv import load_dotenv

load_dotenv(override=True)

DELAY_SECONDS = 1
_original_generate = None


def patch_llm_with_delay(delay: float = DELAY_SECONDS):
    """Monkey-patch ChatGoogleGenerativeAI._generate para adicionar delay e max_retries."""
    global _original_generate

    from langchain_google_genai import ChatGoogleGenerativeAI

    # Aumentar max_retries para permitir esperas mais longas
    ChatGoogleGenerativeAI.model_rebuild()
    ChatGoogleGenerativeAI.model_config["protected_namespaces"] = ()

    _original_generate = ChatGoogleGenerativeAI._generate

    @functools.wraps(ChatGoogleGenerativeAI._generate)
    def _patched_generate(self, *args, **kwargs):
        time.sleep(delay)
        return _original_generate(self, *args, **kwargs)

    ChatGoogleGenerativeAI._generate = _patched_generate
    print(f"✓ Rate limit patch: {delay}s delay entre chamadas")


def patch_max_retries(retries: int = 20):
    """Aumenta max_retries em todas as instâncias de LLM criadas."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    original_init = ChatGoogleGenerativeAI.__init__

    @functools.wraps(original_init)
    def patched_init(self, *args, **kwargs):
        kwargs.setdefault("max_retries", retries)
        original_init(self, *args, **kwargs)

    ChatGoogleGenerativeAI.__init__ = patched_init
    print(f"✓ Max retries configurado para: {retries}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "src")

    patch_llm_with_delay(DELAY_SECONDS)
    patch_max_retries(20)

    from evaluate import main
    sys.exit(main())
