"""Dual Boot Script - Inicia backend e frontend simultaneamente

Uso:
    python dualboot.py              # Inicia backend e frontend com logging integrado
"""

import sys
import os
import subprocess
import threading
import signal
from datetime import datetime


def print_colored(message: str, color: str = "white") -> None:
    """Imprime mensagem com cor no terminal"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    color_code = colors.get(color, colors["white"])
    reset_code = colors["reset"]
    
    print(f"{color_code}[{timestamp}] {message}{reset_code}")


def read_output(process: subprocess.Popen, prefix: str, color: str) -> None:
    """Lê e imprime a saída de um processo em tempo real"""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                print_colored(f"{prefix} {line.rstrip()}", color)
    except Exception as e:
        print_colored(f"{prefix} Erro ao ler saída: {e}", "red")


def read_error(process: subprocess.Popen, prefix: str, color: str) -> None:
    """Lê e imprime os erros de um processo em tempo real"""
    try:
        for line in iter(process.stderr.readline, ''):
            if line:
                print_colored(f"{prefix} {line.rstrip()}", color)
    except Exception as e:
        print_colored(f"{prefix} Erro ao ler stderr: {e}", "red")


def start_backend() -> subprocess.Popen:
    """Inicia o processo do backend"""
    print_colored("Iniciando backend...", "yellow")
    
    backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    boot_script = os.path.join(backend_path, "boot.py")
    
    if not os.path.exists(boot_script):
        print_colored(f"Erro: Arquivo {boot_script} não encontrado", "red")
        sys.exit(1)
    
    process = subprocess.Popen(
        [sys.executable, boot_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=backend_path,
        text=True,
        universal_newlines=True
    )
    
    return process


def start_frontend() -> subprocess.Popen:
    """Inicia o processo do frontend"""
    print_colored("Iniciando frontend...", "yellow")
    
    frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    
    if not os.path.exists(frontend_path):
        print_colored(f"Erro: Diretório {frontend_path} não encontrado", "red")
        sys.exit(1)
    
    # Verificar se node_modules existe
    node_modules = os.path.join(frontend_path, "node_modules")
    if not os.path.exists(node_modules):
        print_colored("node_modules não encontrado. Instalando dependências...", "yellow")
        try:
            subprocess.run(
                "npm install",
                cwd=frontend_path,
                shell=True,
                check=True
            )
            print_colored("Dependências instaladas com sucesso!", "green")
        except subprocess.CalledProcessError as e:
            print_colored(f"Erro ao instalar dependências: {e}", "red")
            sys.exit(1)
    
    # No Windows, usar shell=True para encontrar npm
    shell = True if os.name == 'nt' else False
    
    process = subprocess.Popen(
        "npm run dev",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=frontend_path,
        text=True,
        universal_newlines=True,
        shell=shell
    )
    
    return process


def signal_handler(signum, frame):
    """Handler para encerrar processos gracefully"""
    print_colored("\nRecebido sinal de encerramento. Parando processos...", "yellow")
    sys.exit(0)


def main():
    """Função principal - inicia backend e frontend"""
    print_colored("=" * 60, "cyan")
    print_colored("OpenOB Dual Boot - Backend + Frontend", "cyan")
    print_colored("=" * 60, "cyan")
    
    # Configurar handler para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Iniciar backend
        backend_process = start_backend()
        print_colored(f"Backend iniciado (PID: {backend_process.pid})", "green")
        
        # Iniciar frontend
        frontend_process = start_frontend()
        print_colored(f"Frontend iniciado (PID: {frontend_process.pid})", "green")
        
        print_colored("=" * 60, "cyan")
        print_colored("Ambos os processos iniciados com sucesso!", "green")
        print_colored("Backend: http://localhost:8000", "white")
        print_colored("Frontend: http://localhost:5173", "white")
        print_colored("Pressione Ctrl+C para encerrar ambos", "yellow")
        print_colored("=" * 60, "cyan")
        
        # Iniciar threads para ler saída dos processos
        backend_stdout_thread = threading.Thread(
            target=read_output,
            args=(backend_process, "[BACKEND]", "blue"),
            daemon=True
        )
        backend_stderr_thread = threading.Thread(
            target=read_error,
            args=(backend_process, "[BACKEND-ERR]", "red"),
            daemon=True
        )
        frontend_stdout_thread = threading.Thread(
            target=read_output,
            args=(frontend_process, "[FRONTEND]", "magenta"),
            daemon=True
        )
        frontend_stderr_thread = threading.Thread(
            target=read_error,
            args=(frontend_process, "[FRONTEND-ERR]", "red"),
            daemon=True
        )
        
        # Iniciar threads
        backend_stdout_thread.start()
        backend_stderr_thread.start()
        frontend_stdout_thread.start()
        frontend_stderr_thread.start()
        
        # Aguardar processos
        while True:
            # Verificar se algum processo encerrou
            if backend_process.poll() is not None:
                print_colored("Backend encerrou inesperadamente!", "red")
                break
            
            if frontend_process.poll() is not None:
                print_colored("Frontend encerrou inesperadamente!", "red")
                break
            
            # Pequena pausa para não consumir CPU
            import time
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print_colored("\nEncerrando processos...", "yellow")
    except Exception as e:
        print_colored(f"Erro: {e}", "red")
    finally:
        # Encerrar processos
        if 'backend_process' in locals():
            try:
                backend_process.terminate()
                backend_process.wait(timeout=5)
                print_colored("Backend encerrado", "green")
            except:
                try:
                    backend_process.kill()
                except:
                    pass
        
        if 'frontend_process' in locals():
            try:
                frontend_process.terminate()
                frontend_process.wait(timeout=5)
                print_colored("Frontend encerrado", "green")
            except:
                try:
                    frontend_process.kill()
                except:
                    pass
        
        print_colored("Dual Boot encerrado", "cyan")


if __name__ == "__main__":
    main()
