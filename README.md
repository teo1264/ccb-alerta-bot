# CCB Alerta Bot

Bot do Telegram para gerenciamento de casas de oração, automatizando alertas de consumo excessivo de água (BRK), energia (ENEL) e gerando relatórios mensais de compensação para casas com sistema fotovoltaico.

## Funcionalidades

- Cadastro de responsáveis (cooperadores, encarregados de manutenção, etc.)
- Processo de cadastro passo a passo guiado
- Armazenamento em planilha Excel com colunas adequadamente dimensionadas
- Funções administrativas protegidas
- Interface amigável com mensagens formatadas

## Requisitos

- Python 3.8+
- python-telegram-bot v22.0
- pandas e openpyxl
- pytz

## Instalação

1. Clone o repositório:
```
git clone https://github.com/seu-usuario/ccb-alerta-bot.git
cd ccb-alerta-bot
```

2. Instale as dependências:
```
pip install -r requirements.txt
```

3. Configure o token do bot no arquivo `config.py`

4. Execute o bot:
```
python bot.py
```

## Estrutura do Projeto

- `bot.py` - Arquivo principal de inicialização
- `config.py` - Configurações globais
- `utils.py` - Funções utilitárias
- `handlers/` - Diretório com os manipuladores de comandos e mensagens
  - `commands.py` - Comandos básicos
  - `cadastro.py` - Processo de cadastro
  - `admin.py` - Funções administrativas
  - `mensagens.py` - Processamento de mensagens de texto

## Comandos Disponíveis

- `/start` - Exibe mensagem de boas-vindas e instruções
- `/cadastrar` - Inicia o processo de cadastro passo a passo
- `/cadastro` - Forma alternativa para cadastro manual direto
- `/meu_id` - Mostra o ID do usuário no Telegram
- `/ajuda` - Exibe lista de comandos disponíveis

### Comandos Administrativos

- `/exportar` - Envia a planilha de cadastros
- `/listar` - Lista todos os cadastros
- `/limpar` - Remove todos os cadastros (com confirmação)
- `/admin_add ID` - Adiciona um novo administrador

## Deploy no Render.com

1. Acesse o Render.com e crie um novo serviço "Background Worker"
2. Conecte ao repositório GitHub ou faça upload do código
3. Configure a variável de ambiente `TOKEN` com seu token do Telegram (opcional)
4. Use como comando de build: `pip install -r requirements.txt`
5. Use como comando de start: `python bot.py`

## Suporte e Contato

Para suporte ou dúvidas, entre em contato com o administrador.

---

© 2025 - A Santa Paz de Deus!