import time
import random

def human_sleep(min_s: float = 4.0, max_s: float = 8.0) -> None:
    """Pausa aleatória para simular comportamento humano lento."""
    time.sleep(random.uniform(min_s, max_s))


def short_human_sleep(min_s: float = 1.0, max_s: float = 3.0) -> None:
    """Pausa curta (uso para pequenas ações como confirmar clique)."""
    time.sleep(random.uniform(min_s, max_s))


def look_at_screen_pause(min_s: float = 15.0, max_s: float = 30.0) -> None:
    """Pausa maior entre grupos simulando atenção humana à tela."""
    time.sleep(random.uniform(min_s, max_s))