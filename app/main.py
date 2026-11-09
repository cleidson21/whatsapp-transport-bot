import os
import sys
import time
import json
import random
import logging
import unicodedata
import schedule

# Ensure local timezone (default: America/Bahia, configurable via TZ env)
os.environ.setdefault('TZ', 'America/Bahia')
try:
    time.tzset()
except AttributeError:
    pass

try:
    from app import humanizer
    from app import api_client
except ImportError:
    import humanizer
    import api_client

# ====== LOGGING CONFIGURATION ======
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("whatsapp_bot")


def load_env(env_path=".env"):
    """Loads environment variables from .env file if present and not already defined."""
    search_paths = [
        env_path,
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    ]
    for p in search_paths:
        if os.path.exists(p):
            logger.info(f"Loading environment variables from: {p}")
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
            break


def load_config():
    """Loads configuration from config.json across expected directory paths."""
    search_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"),
        "config.json"
    ]
    for p in search_paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError("Configuration file config.json not found in expected paths.")


def get_shifts_config(config):
    """Retrieves shifts dictionary supporting both English and Portuguese keys."""
    return config.get("shifts") or config.get("turnos") or {}


def get_coordination_group_name(config):
    """Retrieves the coordination group name from environment or config."""
    default = config.get("coordination_group") or config.get("grupo_coordenacao") or "Coordination Dispatch Group"
    return os.getenv("WHATSAPP_COORDINATION_GROUP", default)


def get_shift_details(shifts_data, shift_name):
    """Retrieves details for a shift, supporting shift name aliases."""
    shift_aliases = {
        "morning": ["morning", "matutino"],
        "matutino": ["morning", "matutino"],
        "afternoon": ["afternoon", "vespertino"],
        "vespertino": ["afternoon", "vespertino"],
        "evening": ["evening", "noturno", "night"],
        "noturno": ["evening", "noturno", "night"],
        "saturday": ["saturday", "sabado"],
        "sabado": ["saturday", "sabado"]
    }
    candidates = shift_aliases.get(shift_name.lower(), [shift_name])
    for candidate in candidates:
        if candidate in shifts_data:
            data = shifts_data[candidate]
            schedules = data.get("schedules") or data.get("horarios") or {}
            groups = data.get("groups") or data.get("grupos") or []
            return {
                "name": candidate,
                "groups": groups,
                "schedules": {
                    "open": schedules.get("open") or schedules.get("abrir"),
                    "warn": schedules.get("warn") or schedules.get("avisar"),
                    "close": schedules.get("close") or schedules.get("fechar")
                }
            }
    return None


def normalize_text(text):
    """Removes accents, double spaces, and converts to lower case."""
    if not text:
        return ""
    normalized = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    return " ".join(normalized.lower().split())


def generate_warning_message(group_name, shift, close_time):
    """
    Generates cohesive, varied, and natural warning messages.
    Prevents identical message hashes across groups to protect against Meta spam filters.
    """
    time_str = f"{close_time}" if close_time else "in 30 minutes"
    
    templates = [
        f"⚠️ *Notice*: The roster for *{group_name}* will close at *{time_str}*. If you haven't confirmed your seat yet, please submit your name before the cutoff.",
        f"📢 *Attention Students*: Approximately 30 minutes remaining before roster cutoff for *{group_name}*. Group messaging closes at *{time_str}*.",
        f"⏳ *Reminder*: Roster locking for *{group_name}* is scheduled for *{time_str}*. Please ensure all passenger confirmations are entered.",
        f"🔔 *Transportation Alert*: The boarding roster for *{group_name}* will lock at *{time_str}*. Do not forget to register your seat!",
        f"⚠️ *Official Notice*: Please be reminded that submissions for *{group_name}* are allowed until *{time_str}*. Confirm your seat promptly.",
        f"📢 *Attention Passengers*: Only a few minutes remaining before the *{group_name}* roster cutoff (*{time_str}*). Please verify the list above.",
        f"⏳ *Coordination Dispatch*: Deadline to confirm attendance on *{group_name}* ends at *{time_str}*. Anyone traveling must confirm in time."
    ]
    return random.choice(templates)


def get_closing_message():
    """Returns a subtly randomized closing message to avoid repeated content hashes."""
    templates = [
        "❌✖️❌✖️ *Roster Closed* ❌✖️❌✖️",
        "🔒 *Roster Closed* ❌✖️❌✖️",
        "❌✖️❌✖️ *Submissions Closed* ❌✖️❌✖️",
        "🔒 *Submissions Locked* ❌✖️❌✖️",
        "❌✖️ *Roster Closed* - Time limit reached ❌✖️"
    ]
    return random.choice(templates)


def get_coordination_message(shift):
    """Generates the roster request message directed to the coordination group."""
    shift_labels = {
        "morning": "MORNING",
        "matutino": "MORNING",
        "afternoon": "AFTERNOON",
        "vespertino": "AFTERNOON",
        "evening": "EVENING",
        "noturno": "EVENING",
        "saturday": "SATURDAY",
        "sabado": "SATURDAY"
    }
    label = shift_labels.get(shift.lower(), shift.upper())
    return f"Please dispatch the final student roster for shift: *{label}*."


def find_group_jid(all_groups, target_name):
    """Finds matching group JID by normalized subject comparison."""
    target_norm = normalize_text(target_name)
    for g in all_groups:
        subject = g.get('subject') or g.get('name') or ""
        if normalize_text(subject) == target_norm:
            return g.get('id')
    return None


def run_group_opening(shift):
    """Routine to unlock student groups allowing member messaging."""
    logger.info("=" * 50)
    logger.info(f"STARTING GROUP OPENING - SHIFT: {shift.upper()}")
    logger.info("=" * 50)

    # Initial anti-ban jitter (15s to 45s)
    jitter = random.uniform(15.0, 45.0)
    logger.info(f"Applying randomized opening jitter: {jitter:.1f}s...")
    time.sleep(jitter)

    config = load_config()
    shifts = get_shifts_config(config)
    details = get_shift_details(shifts, shift)
    if not details or not details["groups"]:
        logger.warning(f"No target groups configured for shift '{shift}'.")
        return

    target_groups = details["groups"]
    all_groups = api_client.fetch_all_groups()
    if not all_groups:
        logger.error("Unable to retrieve groups from API. Aborting opening.")
        return

    opened_count = 0
    for i, target_name in enumerate(target_groups):
        logger.info(f"--- Processing opening: {target_name} ---")
        jid = find_group_jid(all_groups, target_name)
        if jid:
            humanizer.short_human_sleep(1.5, 3.5)
            if api_client.update_group_permission(jid, open_chat=True):
                opened_count += 1
        else:
            logger.warning(f"Group '{target_name}' not found on WhatsApp.")

        if i < len(target_groups) - 1:
            humanizer.look_at_screen_pause(12.0, 25.0)

    logger.info(f"Opening Summary ({shift}): {opened_count}/{len(target_groups)} opened.")


def run_group_warning(shift):
    """Routine to send advance cutoff warnings across shift groups."""
    logger.info("=" * 50)
    logger.info(f"STARTING ADVANCE CUTOFF WARNING - SHIFT: {shift.upper()}")
    logger.info("=" * 50)

    # Pre-execution jitter (5s to 20s)
    jitter = random.uniform(5.0, 20.0)
    logger.info(f"Applying randomized warning jitter: {jitter:.1f}s...")
    time.sleep(jitter)

    config = load_config()
    shifts = get_shifts_config(config)
    details = get_shift_details(shifts, shift)
    if not details or not details["groups"]:
        return

    target_groups = details["groups"]
    close_time = details["schedules"].get("close", "")

    all_groups = api_client.fetch_all_groups()
    if not all_groups:
        return

    for i, target_name in enumerate(target_groups):
        logger.info(f"--- Processing warning: {target_name} ---")
        jid = find_group_jid(all_groups, target_name)
        if jid:
            message = generate_warning_message(target_name, shift, close_time)
            typing_delay = random.randint(4000, 7500)
            api_client.send_message(jid, message, delay_ms=typing_delay)

        if i < len(target_groups) - 1:
            humanizer.look_at_screen_pause(15.0, 35.0)


def run_group_closing(shift):
    """
    Roster cutoff routine:
    1. Locks group chat (announcement mode: admins only).
    2. Broadcasts randomized closing notice.
    3. Executes operational cooldown pause (1 to 5 minutes).
    4. Pings coordination dispatch group requesting the finalized list.
    """
    logger.info("=" * 50)
    logger.info(f"STARTING GROUP LOCKING - SHIFT: {shift.upper()}")
    logger.info("=" * 50)

    config = load_config()
    shifts = get_shifts_config(config)
    details = get_shift_details(shifts, shift)
    if not details or not details["groups"]:
        return

    target_groups = details["groups"]
    coordination_group = get_coordination_group_name(config)

    all_groups = api_client.fetch_all_groups()
    if not all_groups:
        return

    # 1. Lock student groups & broadcast closing announcement
    for i, target_name in enumerate(target_groups):
        logger.info(f"--- Processing lock: {target_name} ---")
        jid = find_group_jid(all_groups, target_name)
        if jid:
            if api_client.update_group_permission(jid, open_chat=False):
                humanizer.short_human_sleep(1.0, 2.5)
                delay = random.randint(3000, 5000)
                closing_msg = get_closing_message()
                api_client.send_message(jid, closing_msg, delay_ms=delay)

        if i < len(target_groups) - 1:
            humanizer.look_at_screen_pause(10.0, 20.0)

    # 2. Operational cooldown before pinging dispatch (1 to 5 minutes)
    cooldown_seconds = random.randint(60, 300)
    logger.info(f"Cooling down {cooldown_seconds // 60}m {cooldown_seconds % 60}s before notifying coordination...")
    time.sleep(cooldown_seconds)

    # 3. Notify coordination dispatch group
    jid_coord = find_group_jid(all_groups, coordination_group)
    if jid_coord:
        coord_msg = get_coordination_message(shift)
        api_client.send_message(jid_coord, coord_msg, delay_ms=random.randint(3000, 5000))
        logger.info("Coordination dispatch group notified successfully.")
    else:
        logger.error(f"Coordination group '{coordination_group}' not found.")


def safe_execute(func, shift, action):
    """Executes a routine with exception safety so one failure does not halt the daemon."""
    try:
        func(shift)
    except Exception as e:
        logger.error(f"Error executing '{action}' for shift '{shift}': {e}", exc_info=True)


def register_task(day_name, schedule_time, func, shift_name, action_name):
    """Registers a scheduled job on a given day and hour."""
    if not schedule_time:
        return
    day_scheduler = getattr(schedule.every(), day_name)
    day_scheduler.at(schedule_time).do(safe_execute, func, shift_name, action_name)


def schedule_routines():
    """Parses configuration and registers all shift timers."""
    schedule.clear()
    config = load_config()
    shifts = get_shifts_config(config)

    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    sun_to_thu = ["sunday", "monday", "tuesday", "wednesday", "thursday"]

    # Dispatch day mapping per shift:
    # Morning: opened Mon-Fri, warned & locked the night before (Sun-Thu)
    # Afternoon & Evening: handled same-day Mon-Fri
    # Saturday: opened Thursday, warned & locked Friday
    day_rules = {
        "morning": {"open": weekdays, "warn": sun_to_thu, "close": sun_to_thu},
        "matutino": {"open": weekdays, "warn": sun_to_thu, "close": sun_to_thu},
        "afternoon": {"open": weekdays, "warn": weekdays, "close": weekdays},
        "vespertino": {"open": weekdays, "warn": weekdays, "close": weekdays},
        "evening": {"open": weekdays, "warn": weekdays, "close": weekdays},
        "noturno": {"open": weekdays, "warn": weekdays, "close": weekdays},
        "saturday": {"open": ["thursday"], "warn": ["friday"], "close": ["friday"]},
        "sabado": {"open": ["thursday"], "warn": ["friday"], "close": ["friday"]}
    }

    for shift_name, shift_data in shifts.items():
        schedules = shift_data.get("schedules") or shift_data.get("horarios") or {}
        time_open = schedules.get("open") or schedules.get("abrir")
        time_warn = schedules.get("warn") or schedules.get("avisar")
        time_close = schedules.get("close") or schedules.get("fechar")

        rule = day_rules.get(shift_name.lower(), {"open": weekdays, "warn": weekdays, "close": weekdays})
        for day in rule.get("open", []):
            register_task(day, time_open, run_group_opening, shift_name, "open")
        for day in rule.get("warn", []):
            register_task(day, time_warn, run_group_warning, shift_name, "warn")
        for day in rule.get("close", []):
            register_task(day, time_close, run_group_closing, shift_name, "close")

    logger.info("=" * 60)
    logger.info(f"Scheduling complete: {len(schedule.get_jobs())} active jobs registered:")
    for job in schedule.get_jobs():
        logger.info(f"  • {job}")
    logger.info("=" * 60)


def main():
    load_env()
    logger.info("Starting WhatsApp Transport Hub Bot...")
    schedule_routines()
    logger.info("Entering continuous monitoring loop...")
    while True:
        schedule.run_pending()
        time.sleep(1)


# Backward-compatibility aliases
carregar_env = load_env
carregar_configuracao = load_config
normalizar_texto = normalize_text
executar_abertura = run_group_opening
executar_aviso = run_group_warning
executar_fechamento = run_group_closing
agendar_rotinas = schedule_routines


if __name__ == "__main__":
    main()
