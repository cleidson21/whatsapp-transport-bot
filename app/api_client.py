import os
import logging
from json import JSONDecodeError
import requests

logger = logging.getLogger(__name__)

# Configurações padrão lidas do ambiente
API_URL = os.getenv("WHATSAPP_API_URL", "http://localhost:8080").rstrip("/")
API_KEY = os.getenv("WHATSAPP_API_KEY", "")
API_INSTANCE = os.getenv("WHATSAPP_INSTANCE", "sec-educ-berimbau")


def get_headers():
    return {
        "apikey": os.getenv("WHATSAPP_API_KEY", API_KEY),
        "Content-Type": "application/json"
    }


def get_api_url():
    return os.getenv("WHATSAPP_API_URL", API_URL).rstrip("/")


def get_instance():
    return os.getenv("WHATSAPP_INSTANCE", API_INSTANCE)


def normalizar_lista_grupos(resposta):
    """
    Normaliza a resposta da API que pode retornar diretamente uma lista
    ou um dicionário contendo as chaves 'groups' ou 'data'.
    """
    if isinstance(resposta, dict):
        resposta = resposta.get("groups") or resposta.get("data") or []

    if not isinstance(resposta, list):
        logger.error(f"Resposta inesperada ao buscar grupos: {type(resposta).__name__}")
        return []

    return [grupo for grupo in resposta if isinstance(grupo, dict)]


def buscar_todos_os_grupos():
    """
    Busca a lista de todos os grupos do WhatsApp na instância configurada.
    GET /group/fetchAllGroups/{instance}?getParticipants=false
    """
    url_base = get_api_url()
    instancia = get_instance()
    headers = get_headers()
    url = f"{url_base}/group/fetchAllGroups/{instancia}?getParticipants=false"

    logger.info("🔍 Buscando lista de grupos na Evolution API...")
    try:
        resposta = requests.get(url, headers=headers, timeout=60)
        if resposta.status_code == 200:
            try:
                dados = resposta.json()
                grupos = normalizar_lista_grupos(dados)
                logger.info(f"✅ {len(grupos)} grupos retornados pela API.")
                return grupos
            except JSONDecodeError:
                logger.error("❌ Resposta inválida (não-JSON) ao buscar grupos.")
                return []
        else:
            logger.error(f"⚠️ Erro ao buscar grupos: HTTP {resposta.status_code} - {resposta.text}")
            return []
    except Exception as e:
        logger.error(f"❌ Falha de conexão ao buscar grupos: {e}")
        return []


def atualizar_permissao_grupo(jid, abrir=True):
    """
    Atualiza as permissões de envio de mensagens do grupo.
    POST /group/updateSetting/{instance}
    action: 'not_announcement' (todos falam / abrir)
    action: 'announcement' (somente administradores / fechar)
    """
    url_base = get_api_url()
    instancia = get_instance()
    headers = get_headers()
    url = f"{url_base}/group/updateSetting/{instancia}"

    action = "not_announcement" if abrir else "announcement"
    payload = {
        "groupJid": jid,
        "action": action
    }

    acao_str = "ABRIR" if abrir else "FECHAR"
    logger.info(f"🔒 Enviando comando para {acao_str} o grupo ({jid})...")

    try:
        resposta = requests.post(url, json=payload, headers=headers, timeout=60)
        if resposta.status_code in [200, 201]:
            logger.info(f"✅ Permissão atualizada com sucesso ({acao_str}) no grupo: {jid}")
            return True
        else:
            logger.error(f"⚠️ Erro ao atualizar permissão no grupo {jid}: HTTP {resposta.status_code} - {resposta.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Falha de conexão ao atualizar permissão do grupo {jid}: {e}")
        return False


def enviar_mensagem(jid, texto, delay_ms=None):
    """
    Envia uma mensagem de texto para o JID especificado simulando digitação.
    POST /message/sendText/{instance}
    """
    url_base = get_api_url()
    instancia = get_instance()
    headers = get_headers()
    url = f"{url_base}/message/sendText/{instancia}"

    payload = {
        "number": jid,
        "text": texto,
        "presence": "composing"
    }

    if delay_ms is not None:
        payload["delay"] = int(delay_ms)

    logger.info(f"✉️ Enviando mensagem para {jid}...")
    try:
        resposta = requests.post(url, json=payload, headers=headers, timeout=60)
        if resposta.status_code in [200, 201]:
            logger.info(f"✅ Mensagem enviada com sucesso para {jid}")
            return True
        else:
            logger.error(f"⚠️ Erro ao enviar mensagem para {jid}: HTTP {resposta.status_code} - {resposta.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Falha de conexão ao enviar mensagem para {jid}: {e}")
        return False

