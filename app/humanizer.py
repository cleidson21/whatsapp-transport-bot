import time
import random

def human_sleep(min_s: float = 4.0, max_s: float = 8.0) -> None:
    """Random pause to simulate slow human behavior."""
    time.sleep(random.uniform(min_s, max_s))


def short_human_sleep(min_s: float = 1.0, max_s: float = 3.0) -> None:
    """Short pause for minor actions such as click confirmation or screen transition."""
    time.sleep(random.uniform(min_s, max_s))


def look_at_screen_pause(min_s: float = 15.0, max_s: float = 30.0) -> None:
    """Longer pause between groups simulating human screen reading and attention."""
    time.sleep(random.uniform(min_s, max_s))
