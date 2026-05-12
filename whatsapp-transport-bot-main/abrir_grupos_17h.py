import os
import logging
from json import JSONDecodeError
import requests
import humanizer # Reaproveitando seu script de delays

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

# ====== LISTA DE GRUPOS NOTURNOS (17H) ======
GRUPOS_ALVO = [
    "Transporte SENAI-PITAGORAS Noturno 2026",
    "Transporte UEFS Noturno 2026",
    "Transporte IFBA-UNEF Noturno 2026",
    "Transporte UNIFACS Noturno 2026",
    "Transporte FAT Noturno 2026",
    "Transporte FAN Noturno 2026",
    "Transporte FTC Noturno 2026"
]

def carregar_grupos_alvo(grupos_padrao):
    grupos_env = os.getenv("WHATSAPP_GROUPS")
    if grupos_env:
        grupos = [grupo.strip() for grupo in grupos_env.split(";") if grupo.strip()]
        if grupos:
            return grupos
    return grupos_padrao

def normalizar_lista_grupos(resposta):
    if isinstance(resposta, dict):
        resposta = resposta.get("groups") or resposta.get("data") or []

    if not isinstance(resposta, list):
        logging.error(f"Resposta inesperada ao buscar grupos: {type(resposta).__name__}")
        return []

    return [grupo for grupo in resposta if isinstance(grupo, dict)]

def buscar_todos_os_grupos():
    """Busca a lista de grupos para evitar múltiplas requisições lentas."""
    logging.info("🔍 Sincronizando lista de grupos com a API...")
    url = f"{API_URL}/group/fetchAllGroups/{NOME_INSTANCIA}?getParticipants=false"
    
    try:
        resposta = requests.get(url, headers=headers, timeout=60)
        if resposta.status_code == 200:
            try:
                return normalizar_lista_grupos(resposta.json())
            except JSONDecodeError:
                logging.error("❌ A API devolveu uma resposta inválida ao carregar a lista de grupos.")
                return []
        else:
            logging.error(f"Erro ao buscar grupos: HTTP {resposta.status_code}")
            return []
    except Exception as e:
        logging.error(f"❌ Falha de conexão com o Docker/API: {e}")
        return []

def abrir_permissoes_grupo(jid, nome_grupo):
    """Executa a abertura do grupo para mensagens de todos os membros."""
    url = f"{API_URL}/group/updateSetting/{NOME_INSTANCIA}"
    
    # action: 'not_announcement' -> Libera o envio para membros
    payload = {
        "groupJid": jid,
        "action": "not_announcement" 
    }
    
    try:
        # Verbo POST conforme validado no teste anterior
        resposta = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if resposta.status_code in [200, 201]:
            logging.info(f"✅ SUCESSO: O grupo '{nome_grupo}' está aberto.")
            return True
        else:
            logging.error(f"⚠️ Falha ao abrir '{nome_grupo}': HTTP {resposta.status_code}")
            return False
    except Exception as e:
        logging.error(f"❌ Erro na requisição para '{nome_grupo}': {e}")
        return False

# --- EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    logging.info("=== INICIANDO ROTINA DE ABERTURA (17H) ===")
    
    # Simula o tempo de "abrir o navegador e logar"
    humanizer.short_human_sleep(3.0, 6.0)
    
    # Captura todos os grupos uma única vez
    todos_grupos = buscar_todos_os_grupos()
    grupos_alvo_ativos = carregar_grupos_alvo(GRUPOS_ALVO)
    
    if not todos_grupos:
        logging.error("Não foi possível obter a lista de grupos. Abortando.")
        exit()

    grupos_abertos = 0
    grupos_falhados = []
    
    for i, nome_alvo in enumerate(grupos_alvo_ativos):
        logging.info(f"--- Processando: {nome_alvo} ---")
        
        # Localiza o ID (JID) correspondente ao nome do grupo
        jid_grupo = next((g.get('id') for g in todos_grupos if g.get('subject') == nome_alvo), None)
        
        if jid_grupo:
            # Pausa curta simulando a navegação interna até o menu de permissões
            humanizer.short_human_sleep(2.0, 4.0)
            
            if abrir_permissoes_grupo(jid_grupo, nome_alvo):
                grupos_abertos += 1
            else:
                grupos_falhados.append(nome_alvo)
        else:
            logging.warning(f"⚠️ Grupo '{nome_alvo}' não encontrado. Verifique o nome exato.")
            grupos_falhados.append(nome_alvo)

        # Prevenção Anti-Ban: Pausa longa entre cada grupo
        if i < len(grupos_alvo_ativos) - 1:
            logging.info("⏳ Pausa de segurança (simulando atenção humana)...")
            humanizer.look_at_screen_pause(12.0, 25.0)

    logging.info(f"📊 Resumo Final: {grupos_abertos}/{len(grupos_alvo_ativos)} grupos abertos.")
    if grupos_falhados:
        logging.info(f"❌ Grupos com falha: {grupos_falhados}")
        
    logging.info("🏁 Operação de 17h concluída com sucesso.")