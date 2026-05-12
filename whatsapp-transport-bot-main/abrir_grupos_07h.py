import os
import logging
from json import JSONDecodeError
import requests
import humanizer # Reaproveitando o seu módulo de pausas aleatórias!

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

# ====== LISTA DE GRUPOS (07H) ======
GRUPOS_ALVO = [
    "Transporte UEFS/ FTC/ UFRB 2026",
    "Transporte IFBA-UNEF Matutino 2026",
    "Transporte Matutino (Centro) 2026"
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
    """Busca a lista de grupos UMA ÚNICA VEZ para evitar spam no servidor da Meta."""
    logging.info("🔍 A descarregar a lista de todos os grupos do WhatsApp...")
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
        logging.error(f"❌ Falha de conexão: {e}")
        return []

def abrir_permissoes_grupo(jid, nome_grupo):
    """Envia o comando POST para permitir que todos enviem mensagens."""
    url = f"{API_URL}/group/updateSetting/{NOME_INSTANCIA}"
    
    # action: 'not_announcement' -> Abre o grupo
    payload = {
        "groupJid": jid,
        "action": "not_announcement" 
    }
    
    try:
        # Usando o verbo POST, como corrigimos no passo anterior!
        resposta = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if resposta.status_code in [200, 201]:
            logging.info(f"✅ SUCESSO! O grupo '{nome_grupo}' foi ABERTO.")
            return True
        else:
            logging.error(f"⚠️ Erro ao abrir '{nome_grupo}': HTTP {resposta.status_code} - {resposta.text}")
            return False
    except Exception as e:
        logging.error(f"❌ Falha ao enviar o comando para '{nome_grupo}': {e}")
        return False

# --- EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    logging.info("=== INICIANDO ABERTURA DE GRUPOS (07H) ===")
    
    # Pausa inicial de segurança para simular alguém a abrir o telemóvel
    humanizer.short_human_sleep(2.0, 5.0)
    
    # 1º Passo: Carregar todos os grupos para a memória
    todos_grupos = buscar_todos_os_grupos()
    grupos_alvo_ativos = carregar_grupos_alvo(GRUPOS_ALVO)
    
    if not todos_grupos:
        logging.error("A lista de grupos está vazia. Cancelando a operação de abertura.")
        exit()

    grupos_abertos = 0
    grupos_falhados = []
    
    for i, nome_alvo in enumerate(grupos_alvo_ativos):
        logging.info(f"--- Processando: {nome_alvo} ---")
        
        # Procura o JID do grupo alvo na lista que já baixámos
        jid_grupo = next((g.get('id') for g in todos_grupos if g.get('subject') == nome_alvo), None)
        
        if jid_grupo:
            # Encontrou o JID! Simula a leitura e clique no ecrã antes de abrir
            humanizer.short_human_sleep(1.5, 3.5)
            
            if abrir_permissoes_grupo(jid_grupo, nome_alvo):
                grupos_abertos += 1
            else:
                grupos_falhados.append(nome_alvo)
        else:
            logging.warning(f"⚠️ Grupo '{nome_alvo}' não encontrado na lista do WhatsApp.")
            grupos_falhados.append(nome_alvo)

        # 2º Passo Crítico (ANTI-BAN): Pausa longa entre um grupo e outro
        # Só aplicamos a pausa longa se não for o último grupo da lista
        if i < len(grupos_alvo_ativos) - 1:
            logging.info("⏳ A simular transição entre grupos (Prevenção Anti-Ban)...")
            humanizer.look_at_screen_pause(10.0, 20.0)

    logging.info(f"📊 Resumo: {grupos_abertos}/{len(grupos_alvo_ativos)} grupos abertos.")
    if grupos_falhados:
        logging.info(f"Falhados: {grupos_falhados}")
        
    logging.info("🏁 Rotina (07H) finalizada com segurança e sucesso.")