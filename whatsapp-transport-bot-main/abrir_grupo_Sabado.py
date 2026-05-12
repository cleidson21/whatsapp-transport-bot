import os
import time
import logging
from json import JSONDecodeError
import requests

# ====== CONFIGURAÇÃO DE LOGS ======
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_api_automacao.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ====== CONFIGURAÇÕES DA API ======
API_URL = os.getenv("WHATSAPP_API_URL", "http://localhost:8080")
API_KEY = os.getenv("WHATSAPP_API_KEY", "Transporte_Universitario_2026_Secreta")
NOME_INSTANCIA = os.getenv("WHATSAPP_INSTANCE", "sec-educ-berimbau")

headers = {
    "apikey": API_KEY,
    "Content-Type": "application/json"
}

# ====== LISTA DE GRUPOS ======
GRUPOS_ALVO = [
    grupo.strip()
    for grupo in os.getenv("WHATSAPP_GROUPS", "Transporte UEFS Sábado 2026").split(";")
    if grupo.strip()
]

def buscar_jid_do_grupo(nome_grupo_alvo):
    """Consulta a API para encontrar o ID interno (JID) do grupo pelo nome."""
    logging.info(f"🔍 A buscar o ID interno do grupo: '{nome_grupo_alvo}'...")
    url = f"{API_URL}/group/fetchAllGroups/{NOME_INSTANCIA}?getParticipants=false"
    
    try:
        resposta = requests.get(url, headers=headers, timeout=60)
        
        if resposta.status_code != 200:
            logging.error(f"Erro ao buscar grupos: HTTP {resposta.status_code} - {resposta.text}")
            return None
            
        grupos = resposta.json()
        if isinstance(grupos, dict):
            grupos = grupos.get("groups") or grupos.get("data") or []

        if not isinstance(grupos, list):
            logging.error(f"Resposta inesperada ao buscar grupos: {type(grupos).__name__}")
            return None
        
        for grupo in grupos:
            if not isinstance(grupo, dict):
                continue

            if grupo.get('subject') == nome_grupo_alvo:
                jid = grupo.get('id') or grupo.get('jid')
                if not jid:
                    logging.warning(f"⚠️ O grupo '{nome_grupo_alvo}' foi encontrado, mas sem JID válido na resposta.")
                    return None
                logging.info(f"✅ Grupo encontrado! JID interno: {jid}")
                return jid
                
        logging.warning(f"⚠️ Grupo '{nome_grupo_alvo}' não encontrado. Verifique se o nome está exato e se o bot está no grupo.")
        return None
        
    except JSONDecodeError:
        logging.error(f"❌ A API devolveu uma resposta inválida ao procurar o grupo '{nome_grupo_alvo}'.")
        return None
    except Exception as e:
        logging.error(f"❌ Falha de conexão com a API: {e}")
        return None

def abrir_permissoes_grupo(jid, nome_grupo):
    """Envia o comando direto para permitir que todos os membros enviem mensagens."""
    logging.info(f"🔓 A enviar ordem para ABRIR o grupo '{nome_grupo}'...")
    url = f"{API_URL}/group/updateSetting/{NOME_INSTANCIA}"
    
    # action: 'not_announcement' -> Abre o grupo para todos
    payload = {
        "groupJid": jid,
        "action": "not_announcement" 
    }
    
    try:
        resposta = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if resposta.status_code in [200, 201]:
            logging.info(f"✅ SUCESSO ABSOLUTO! O grupo '{nome_grupo}' foi aberto.")
            return True
        else:
            logging.error(f"⚠️ Erro ao alterar permissões: HTTP {resposta.status_code} - {resposta.text}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Falha ao enviar o comando de abertura: {e}")
        return False

# --- EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    logging.info("=== INICIANDO ABERTURA DE GRUPOS VIA API (SÁBADO) ===")
    
    grupos_abertos = 0
    grupos_falhados = []
    
    for grupo in GRUPOS_ALVO:
        logging.info(f"--- Processando: {grupo} ---")
        
        jid_grupo = buscar_jid_do_grupo(grupo)
        
        if jid_grupo:
            if abrir_permissoes_grupo(jid_grupo, grupo):
                grupos_abertos += 1
            else:
                grupos_falhados.append(grupo)
        else:
            grupos_falhados.append(grupo)

    logging.info(f"📊 Resumo: {grupos_abertos}/{len(GRUPOS_ALVO)} grupos abertos instantaneamente.")
    if grupos_falhados:
        logging.info(f"Falhados: {grupos_falhados}")
        
    logging.info("🏁 Rotina finalizada com sucesso.")