#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de instalação para o CCB Alerta Bot
Este script auxilia na configuração inicial do bot
"""

import os
import sys
import subprocess
import shutil
import time

def print_header():
    """Exibe o cabeçalho do instalador"""
    print("\n")
    print("=" * 60)
    print(" 🤖  CCB ALERTA BOT - ASSISTENTE DE INSTALAÇÃO")
    print("=" * 60)
    print(" 🕊️  A Santa Paz de Deus!")
    print("-" * 60)
    print(" Este assistente vai ajudar você a configurar o bot.\n")

def check_python_version():
    """Verifica se a versão do Python é compatível"""
    print("🔍 Verificando versão do Python...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Erro: É necessário Python 3.8 ou superior!")
        print(f"   Versão atual: Python {version.major}.{version.minor}.{version.micro}")
        print("   Por favor, instale uma versão mais recente do Python e tente novamente.")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK!")
    return True

def create_virtual_env():
    """Cria um ambiente virtual Python"""
    print("\n🔧 Criando ambiente virtual Python...")
    
    # Verificar se venv já existe
    if os.path.exists("venv"):
        choice = input("   Ambiente virtual já existe. Recriar? [s/N]: ").lower()
        if choice == 's' or choice == 'sim':
            try:
                shutil.rmtree("venv")
                print("   Ambiente anterior removido.")
            except:
                print("❌ Erro ao remover ambiente existente.")
                return False
        else:
            print("✅ Usando ambiente virtual existente.")
            return True
    
    # Criar novo venv
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Ambiente virtual criado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar ambiente virtual: {e}")
        return False

def install_dependencies():
    """Instala as dependências necessárias"""
    print("\n🔧 Instalando dependências...")
    
    # Determinar o executável pip correto
    pip_cmd = os.path.join("venv", "Scripts", "pip") if os.name == "nt" else os.path.join("venv", "bin", "pip")
    
    try:
        # Upgrade pip
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
        
        # Instalar dependências
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependências instaladas com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def configure_bot():
    """Configura o token do bot"""
    print("\n🔧 Configurando o bot...")
    
    try:
        from config import TOKEN
        token = TOKEN
    except:
        token = "SEU_TOKEN_AQUI"
    
    if token == "SEU_TOKEN_AQUI" or token == "7773179413:AAHqJp-NBPPs6YrSV1kB5-q4vkV3tjDFyy4":
        print("⚠️  O token do bot precisa ser configurado.")
        new_token = input("   Digite o token do seu bot (obtido do @BotFather): ")
        
        if new_token.strip():
            try:
                with open("config.py", "r", encoding="utf-8") as f:
                    content = f.read()
                
                content = content.replace(f'TOKEN = "{token}"', f'TOKEN = "{new_token}"')
                
                with open("config.py", "w", encoding="utf-8") as f:
                    f.write(content)
                
                print("✅ Token configurado com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao configurar token: {e}")
                return False
        else:
            print("⚠️  Nenhum token fornecido. Você precisará editar o arquivo config.py manualmente.")
    else:
        print("✅ Bot já está configurado com um token.")
    
    # Criar pasta de logs
    if not os.path.exists("logs"):
        os.makedirs("logs")
        print("✅ Pasta de logs criada.")
    
    return True

def create_start_script():
    """Cria scripts para iniciar o bot"""
    print("\n🔧 Criando scripts de inicialização...")
    
    # Script para Windows (batch)
    try:
        with open("start_bot.bat", "w") as f:
            f.write("@echo off\n")
            f.write("echo Iniciando CCB Alerta Bot...\n")
            f.write("call venv\\Scripts\\activate\n")
            f.write("python bot.py\n")
            f.write("pause\n")
        
        print("✅ Script start_bot.bat criado para Windows.")
    except Exception as e:
        print(f"❌ Erro ao criar script para Windows: {e}")
    
    # Script para Linux/macOS (shell)
    try:
        with open("start_bot.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write("echo \"Iniciando CCB Alerta Bot...\"\n")
            f.write("source venv/bin/activate\n")
            f.write("python bot.py\n")
        
        # Tornar o script executável
        if os.name != "nt":  # Se não for Windows
            os.chmod("start_bot.sh", 0o755)
        
        print("✅ Script start_bot.sh criado para Linux/macOS.")
    except Exception as e:
        print(f"❌ Erro ao criar script para Linux/macOS: {e}")
    
    return True

def main():
    """Função principal do instalador"""
    print_header()
    
    if not check_python_version():
        input("\nPressione ENTER para sair...")
        sys.exit(1)
    
    if not create_virtual_env():
        input("\nPressione ENTER para sair...")
        sys.exit(1)
    
    if not install_dependencies():
        input("\nPressione ENTER para sair...")
        sys.exit(1)
    
    if not configure_bot():
        print("\n⚠️  Configuração parcial. Você pode precisar ajustar manualmente o arquivo config.py.")
    
    create_start_script()
    
    print("\n" + "=" * 60)
    print(" ✅  INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print("\n Para iniciar o bot:")
    print(" - Windows: Execute o arquivo start_bot.bat")
    print(" - Linux/macOS: Execute ./start_bot.sh")
    print("\n 🙏 Deus te abençoe!")
    print("-" * 60)
    
    input("\nPressione ENTER para sair...")

if __name__ == "__main__":
    main()