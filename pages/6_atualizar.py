import os
import subprocess
import threading
import time
from queue import Empty, Queue

import streamlit as st

from src.utils.get_date import get_last_update_date

st.set_page_config(page_title="Atualizar", layout="wide")

# Caminho do Python do ambiente virtual
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
VENV_PYTHON = os.path.join(PROJECT_ROOT, ".venv", "bin", "python")
SCRIPT_PATH = os.path.join(PROJECT_ROOT, "src", "scrapes", "all_scrapes.py")

# Verifica se o ambiente virtual existe
if not os.path.exists(VENV_PYTHON):
    st.error(f"Ambiente virtual não encontrado em: {VENV_PYTHON}")
    st.info("Certifique-se de que o ambiente virtual `.venv` está criado e ativado.")
    st.stop()

# Verifica se o script existe
if not os.path.exists(SCRIPT_PATH):
    st.error(f"Script não encontrado em: {SCRIPT_PATH}")
    st.stop()

st.title("Atualizar Dados")

# Inicializa o estado da sessão
if "process_running" not in st.session_state:
    st.session_state.process_running = False

if "logs" not in st.session_state:
    st.session_state.logs = []

if "process" not in st.session_state:
    st.session_state.process = None

if "return_code" not in st.session_state:
    st.session_state.return_code = None

if "log_queue" not in st.session_state:
    st.session_state.log_queue = Queue()

if "just_finished" not in st.session_state:
    st.session_state.just_finished = False


def enqueue_output(process, queue):
    """Lê a saída do processo e coloca na fila"""
    for line in iter(process.stdout.readline, ""):
        if line:
            queue.put(line.strip())
    process.stdout.close()


def run_scrapes(selected_scrapes):
    """Executa o script de scrapes com os argumentos selecionados"""
    st.session_state.process_running = True
    st.session_state.logs = []
    st.session_state.return_code = None
    st.session_state.log_queue = Queue()

    try:
        # Constrói o comando com os argumentos selecionados
        cmd = [VENV_PYTHON, SCRIPT_PATH]

        # Se nenhum scrape foi selecionado ou todos foram selecionados, usa --all
        if not selected_scrapes or len(selected_scrapes) == 5:
            cmd.append("--all")
        else:
            # Adiciona os argumentos correspondentes aos scrapes selecionados
            if "investidor10_fiis" in selected_scrapes:
                cmd.append("--investidor10-fiis")
            if "investidor10_dividends" in selected_scrapes:
                cmd.append("--investidor10-dividends")
            if "fundamentus" in selected_scrapes:
                cmd.append("--fundamentus")
            if "fnet" in selected_scrapes:
                cmd.append("--fnet")
            if "ward" in selected_scrapes:
                cmd.append("--ward")

        # Executa o script usando o Python do ambiente virtual
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            cwd=PROJECT_ROOT,
        )

        st.session_state.process = process

        # Thread para ler a saída em tempo real
        thread = threading.Thread(
            target=enqueue_output, args=(process, st.session_state.log_queue), daemon=True
        )
        thread.start()

    except Exception as e:
        st.session_state.logs.append(f"Erro ao executar script: {str(e)}")
        st.session_state.process_running = False
        st.session_state.return_code = -1


def _process_log_queue():
    """Processa logs da fila e adiciona ao estado."""
    while True:
        try:
            log_line = st.session_state.log_queue.get_nowait()
            if log_line:
                st.session_state.logs.append(log_line)
                # Limita o número de linhas de log para evitar uso excessivo de memória
                if len(st.session_state.logs) > 1000:
                    st.session_state.logs = st.session_state.logs[-1000:]
        except Empty:
            break


def _read_remaining_logs():
    """Lê qualquer saída restante após o processo terminar."""
    try:
        while True:
            log_line = st.session_state.log_queue.get_nowait()
            if log_line:
                st.session_state.logs.append(log_line)
    except Empty:
        pass


def _handle_process_completion(return_code):
    """Lida com a conclusão do processo."""
    st.session_state.return_code = return_code
    st.session_state.process_running = False
    st.session_state.process = None

    # Se a atualização foi bem-sucedida, aguarda um momento e limpa o cache do Streamlit
    # Isso garante que os arquivos CSV foram completamente escritos no disco
    if return_code == 0:
        # Aguarda um pouco mais para garantir que os arquivos foram completamente escritos
        time.sleep(2)
        # Limpa todo o cache do Streamlit para forçar recarregamento dos dados
        st.cache_data.clear()
        st.session_state.just_finished = True
        # Força um rerun para atualizar a data exibida
        st.rerun()
    else:
        st.session_state.just_finished = False


def _check_and_process_logs():
    """Verifica se há novos logs na fila e processa o estado do processo."""
    if not (st.session_state.process_running and st.session_state.process):
        return

    try:
        _process_log_queue()

        # Verifica se o processo terminou
        return_code = st.session_state.process.poll()
        if return_code is not None:
            # Processo terminou, lê qualquer saída restante
            _read_remaining_logs()
            _handle_process_completion(return_code)

    except Exception as e:
        st.session_state.logs.append(f"Erro ao ler logs: {str(e)}")


# Verifica se há novos logs na fila e adiciona ao estado
_check_and_process_logs()


# Calcula a data de atualização após verificar o estado do processo
# Se a atualização acabou de completar, força recarregamento sem cache
# Também força recarregamento se acabamos de limpar o cache
if st.session_state.just_finished:
    # Força recarregamento direto sem cache após atualização
    atualizado = get_last_update_date(use_cache=False)
    st.session_state.just_finished = False  # Reseta após usar
else:
    atualizado = get_last_update_date(use_cache=True)

st.sidebar.text(f"Atualizado {atualizado}")

# Botão para iniciar/parar a execução
col1, col2 = st.columns([1, 4])

with col1:
    if st.session_state.process_running:
        if st.button("⏹️ Parar", type="primary"):
            if st.session_state.process:
                st.session_state.process.terminate()
                st.session_state.process_running = False
                st.session_state.logs.append("Processo interrompido pelo usuário")
                st.session_state.process = None
                st.rerun()
    else:
        if st.button("▶️ Iniciar Atualização", type="primary"):
            # Sempre executa todos os scrapes (selected_scrapes vazio usa --all)
            run_scrapes([])
            st.rerun()

with col2:
    if st.session_state.process_running:
        st.info("Processo em execução...")
    elif st.session_state.return_code == 0:
        st.success("Atualização concluída com sucesso!")
    elif st.session_state.return_code is not None and st.session_state.return_code != 0:
        st.error(f"Processo finalizado com código de erro: {st.session_state.return_code}")

# Exibe os logs
st.markdown("### Logs de Execução")

if st.session_state.logs:
    # Mostra os últimos 200 logs
    display_logs = st.session_state.logs[-200:]
    st.code("\n".join(display_logs), language="text")

    # Botão para limpar logs
    if st.button("🗑️ Limpar Logs"):
        st.session_state.logs = []
        st.rerun()
else:
    st.info("Sem logs no momento, execute a atualização ou aguarde alguns segundos.")

# Atualiza automaticamente enquanto o processo está rodando
if st.session_state.process_running:
    time.sleep(0.5)  # Pequeno delay antes de atualizar
    st.rerun()
