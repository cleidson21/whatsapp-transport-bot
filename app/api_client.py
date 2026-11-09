import os
import logging
from json import JSONDecodeError
import requests

logger = logging.getLogger(__name__)

# Default API configuration read from environment
API_URL = os.getenv("WHATSAPP_API_URL", "http://localhost:8080").rstrip("/")
API_KEY = os.getenv("WHATSAPP_API_KEY", "")
API_INSTANCE = os.getenv("WHATSAPP_INSTANCE", "transporte-hub")


def get_headers():
    return {
        "apikey": os.getenv("WHATSAPP_API_KEY", API_KEY),
        "Content-Type": "application/json"
    }


def get_api_url():
    return os.getenv("WHATSAPP_API_URL", API_URL).rstrip("/")


def get_instance():
    return os.getenv("WHATSAPP_INSTANCE", API_INSTANCE)


def normalize_group_list(response_data):
    """
    Normalizes the API response, handling both direct lists or dictionaries
    containing 'groups' or 'data' keys.
    """
    if isinstance(response_data, dict):
        response_data = response_data.get("groups") or response_data.get("data") or []

    if not isinstance(response_data, list):
        logger.error(f"Unexpected response format while fetching groups: {type(response_data).__name__}")
        return []

    return [group for group in response_data if isinstance(group, dict)]


def fetch_all_groups():
    """
    Retrieves all WhatsApp groups for the configured instance.
    GET /group/fetchAllGroups/{instance}?getParticipants=false
    """
    base_url = get_api_url()
    instance = get_instance()
    headers = get_headers()
    url = f"{base_url}/group/fetchAllGroups/{instance}?getParticipants=false"

    logger.info("🔍 Fetching group list from Evolution API...")
    try:
        response = requests.get(url, headers=headers, timeout=60)
        if response.status_code == 200:
            try:
                data = response.json()
                groups = normalize_group_list(data)
                logger.info(f"✅ {len(groups)} groups retrieved from API.")
                return groups
            except JSONDecodeError:
                logger.error("❌ Invalid non-JSON response while fetching groups.")
                return []
        else:
            logger.error(f"⚠️ Error fetching groups: HTTP {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"❌ Connection error while fetching groups: {e}")
        return []


def update_group_permission(jid, open_chat=True):
    """
    Updates group messaging permissions.
    POST /group/updateSetting/{instance}
    action: 'not_announcement' (everyone can send / open)
    action: 'announcement' (admins only / close)
    """
    base_url = get_api_url()
    instance = get_instance()
    headers = get_headers()
    url = f"{base_url}/group/updateSetting/{instance}"

    action = "not_announcement" if open_chat else "announcement"
    payload = {
        "groupJid": jid,
        "action": action
    }

    action_label = "OPEN" if open_chat else "LOCK"
    logger.info(f"🔒 Sending command to {action_label} group ({jid})...")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        if response.status_code in [200, 201]:
            logger.info(f"✅ Group permission updated ({action_label}) for: {jid}")
            return True
        else:
            logger.error(f"⚠️ Error updating permissions for group {jid}: HTTP {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Connection error while updating permissions for {jid}: {e}")
        return False


def send_message(jid, text, delay_ms=None):
    """
    Sends a text message to a WhatsApp JID with typing presence simulation.
    POST /message/sendText/{instance}
    """
    base_url = get_api_url()
    instance = get_instance()
    headers = get_headers()
    url = f"{base_url}/message/sendText/{instance}"

    payload = {
        "number": jid,
        "text": text,
        "presence": "composing"
    }

    if delay_ms is not None:
        payload["delay"] = int(delay_ms)

    logger.info(f"✉️ Sending message to {jid}...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        if response.status_code in [200, 201]:
            logger.info(f"✅ Message delivered successfully to {jid}")
            return True
        else:
            logger.error(f"⚠️ Error sending message to {jid}: HTTP {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Connection error while sending message to {jid}: {e}")
        return False


# Backward-compatibility aliases
buscar_todos_os_grupos = fetch_all_groups
atualizar_permissao_grupo = update_group_permission
enviar_mensagem = send_message
normalizar_lista_grupos = normalize_group_list
