import os
import sys
import time
import json
import random
import logging
import unicodedata
import schedule

# Garante fuso horário local oficial da Bahia
os.environ['TZ'] = 'America/Bahia'
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

# ====== CONFIGURAÇÃO DE LOGS ======
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("whatsapp_bot")

def carregar_env(caminho=".env"):
    """Carrega variáveis do arquivo .env se presente e não definido no ambiente."""
    caminhos = [
        caminho,
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    ]
    for p in caminhos:
        if os.path.exists(p):
            logger.info(f"Carregando variáveis de ambiente de: {p}")
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

def carregar_configuracao():
    """Carrega as configurações a partir do arquivo config.json."""
    caminhos = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"),
        "config.json"
    ]
    for p in caminhos:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError("Arquivo config.json não encontrado nas rotas esperadas.")

def normalizar_texto(texto):
    """Remove acentos, espaços duplicados e converte para minúsculas."""
    if not texto:
        return ""
    texto_norm = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return " ".join(texto_norm.lower().split())

MENSAGEM_FECHAMENTO = "❌✖️❌✖️ *Lista Fechada* ❌✖️❌✖️"

def obter_mensagem_aviso(turno):
    if turno.lower() == "matutino":
        return "⚠️ *Aviso Sistema*: Lista Matutina fecha em 30 minutos!"
    return f"⚠️ *Aviso Sistema*: Lista {turno.capitalize()} fecha em 30 minutos!"

def obter_mensagem_coordenacao(turno):
    nomes = {
        "matutino": "MATUTINO",
        "vespertino": "VESPERTINO",
        "noturno": "NOTURNO",
        "sabado": "SÁBADO"
    }
    nome_fmt = nomes.get(turno.lower(), turno.upper())
    return f"Por favor, enviar a lista do turno fechado: *{nome_fmt}*."

def encontrar_jid_grupo(todos_grupos, nome_procurado):
    alvo_norm = normalizar_texto(nome_procurado)
    for g in todos_grupos:
        nome_grupo = g.get('subject') or g.get('name') or ""
        if normalizar_texto(nome_grupo) == alvo_norm:
            return g.get('id')
    return None

def executar_abertura(turno):
    logger.info("=" * 50)
    logger.info(f"INICIANDO ABERTURA DE GRUPOS - TURNO: {turno.upper()}")
    logger.info("=" * 50)

    delay_jitter = random.uniform(15.0, 45.0)
    logger.info(f"Aguardando jitter humano de {delay_jitter:.1f}s...")
    time.sleep(delay_jitter)

    config = carregar_configuracao()
    grupos_alvo = config.get("turnos", {}).get(turno, {}).get("grupos", [])
    if not grupos_alvo:
        logger.warning(f"Nenhum grupo configurado para o turno '{turno}'.")
        return

    todos_grupos = api_client.buscar_todos_os_grupos()
    if not todos_grupos:
        logger.error("Não foi possível obter grupos da API.")
        return

    abertos = 0
    for i, nome_alvo in enumerate(grupos_alvo):
        logger.info(f"--- Processando abertura: {nome_alvo} ---")
        jid = encontrar_jid_grupo(todos_grupos, nome_alvo)
        if jid:
            humanizer.short_human_sleep(1.5, 3.5)
            if api_client.atualizar_permissao_grupo(jid, abrir=True):
                abertos += 1
        else:
            logger.warning(f"Grupo '{nome_alvo}' não encontrado no WhatsApp.")

        if i < len(grupos_alvo) - 1:
            humanizer.look_at_screen_pause(10.0, 20.0)

    logger.info(f"Resumo Abertura ({turno}): {abertos}/{len(grupos_alvo)} abertos.")

def executar_aviso(turno):
    logger.info("=" * 50)
    logger.info(f"INICIANDO AVISO DE FECHAMENTO - TURNO: {turno.upper()}")
    logger.info("=" * 50)

    config = carregar_configuracao()
    grupos_alvo = config.get("turnos", {}).get(turno, {}).get("grupos", [])
    if not grupos_alvo:
        return

    todos_grupos = api_client.buscar_todos_os_grupos()
    if not todos_grupos:
        return

    msg = obter_mensagem_aviso(turno)
    for i, nome_alvo in enumerate(grupos_alvo):
        logger.info(f"--- Processando aviso: {nome_alvo} ---")
        jid = encontrar_jid_grupo(todos_grupos, nome_alvo)
        if jid:
            delay = random.randint(3000, 6000)
            api_client.enviar_mensagem(jid, msg, delay_ms=delay)

        if i < len(grupos_alvo) - 1:
            humanizer.look_at_screen_pause(10.0, 20.0)

def executar_fechamento(turno):
    logger.info("=" * 50)
    logger.info(f"INICIANDO FECHAMENTO DE GRUPOS - TURNO: {turno.upper()}")
    logger.info("=" * 50)

    config = carregar_configuracao()
    grupos_alvo = config.get("turnos", {}).get(turno, {}).get("grupos", [])
    grupo_coord = os.getenv("WHATSAPP_COORDINATION_GROUP", config.get("grupo_coordenacao", "Operação Transporte Universitário"))

    todos_grupos = api_client.buscar_todos_os_grupos()
    if not todos_grupos:
        return

    # 1. Trancar grupos e mandar aviso
    for i, nome_alvo in enumerate(grupos_alvo):
        logger.info(f"--- Processando fechamento: {nome_alvo} ---")
        jid = encontrar_jid_grupo(todos_grupos, nome_alvo)
        if jid:
            if api_client.atualizar_permissao_grupo(jid, abrir=False):
                humanizer.short_human_sleep(1.0, 2.5)
                delay = random.randint(3000, 5000)
                api_client.enviar_mensagem(jid, MENSAGEM_FECHAMENTO, delay_ms=delay)

        if i < len(grupos_alvo) - 1:
            humanizer.look_at_screen_pause(10.0, 18.0)

    # 2. Pausa humanizada antes da coordenação
    espera_segundos = random.randint(60, 300)
    logger.info(f"Aguardando pausa operacional de {espera_segundos // 60}m {espera_segundos % 60}s antes de pedir lista...")
    time.sleep(espera_segundos)

    # 3. Notificar coordenação
    jid_coord = encontrar_jid_grupo(todos_grupos, grupo_coord)
    if jid_coord:
        msg_coord = obter_mensagem_coordenacao(turno)
        api_client.enviar_mensagem(jid_coord, msg_coord, delay_ms=random.randint(3000, 5000))
        logger.info("Mensagem enviada para a Coordenação com sucesso.")
    else:
        logger.error(f"Grupo de Coordenação '{grupo_coord}' não foi encontrado.")

def executar_com_seguranca(funcao, turno, acao):
    """Garante que falhas isoladas de rede/API não interrompam o agendador global."""
    try:
        funcao(turno)
    except Exception as e:
        logger.error(f"Erro ao executar '{acao}' do turno '{turno}': {e}", exc_info=True)

def registrar_tarefa(dia_nome, horario, funcao, turno_nome, acao_nome):
    """Cria uma instância isolada no agendador para cada combinação de dia e horário."""
    if not horario:
        return
    agendador_dia = getattr(schedule.every(), dia_nome)
    agendador_dia.at(horario).do(executar_com_seguranca, funcao, turno_nome, acao_nome)

def agendar_rotinas():
    schedule.clear()
    config = carregar_configuracao()
    turnos = config.get("turnos", {})

    dias_semana = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    dias_dom_a_qui = ["sunday", "monday", "tuesday", "wednesday", "thursday"]

    # Mapeamento estrito das regras operacionais
    regras = {
        "matutino": {
            "abrir": dias_semana,
            "avisar": dias_dom_a_qui,
            "fechar": dias_dom_a_qui
        },
        "vespertino": {
            "abrir": dias_semana,
            "avisar": dias_semana,
            "fechar": dias_semana
        },
        "noturno": {
            "abrir": dias_semana,
            "avisar": dias_semana,
            "fechar": dias_semana
        },
        "sabado": {
            "abrir": ["thursday"],
            "avisar": ["friday"],
            "fechar": ["friday"]
        }
    }

    for turno_nome, dados in turnos.items():
        horarios = dados.get("horarios", {})
        h_abrir = horarios.get("abrir")
        h_avisar = horarios.get("avisar")
        h_fechar = horarios.get("fechar")

        regra_turno = regras.get(turno_nome, {})
        for dia in regra_turno.get("abrir", []):
            registrar_tarefa(dia, h_abrir, executar_abertura, turno_nome, "abertura")
        for dia in regra_turno.get("avisar", []):
            registrar_tarefa(dia, h_avisar, executar_aviso, turno_nome, "aviso")
        for dia in regra_turno.get("fechar", []):
            registrar_tarefa(dia, h_fechar, executar_fechamento, turno_nome, "fechamento")

    logger.info("=" * 60)
    logger.info(f"Agendamento concluído: {len(schedule.get_jobs())} tarefas ativas na grade:")
    for job in schedule.get_jobs():
        logger.info(f"  • {job}")
    logger.info("=" * 60)

def main():
    carregar_env()
    logger.info("Iniciando WhatsApp Transport Hub Bot...")
    agendar_rotinas()
    logger.info("Monitorando horários...")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()