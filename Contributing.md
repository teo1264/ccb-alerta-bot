# Guia de Contribuição

Obrigado por seu interesse em contribuir com o CCB Alerta Bot! Este documento fornece diretrizes para contribuir com o projeto.

## Código de Conduta

Todos os colaboradores devem seguir estes princípios:

- Tratar todos com respeito e cordialidade
- Aceitar críticas construtivas
- Focar no que é melhor para a comunidade
- Mostrar empatia com outros membros da comunidade

## Como Contribuir

### Reportando Bugs

Se você encontrar um bug, por favor, crie uma issue detalhando:

1. Passos para reproduzir o bug
2. Comportamento esperado vs. comportamento observado
3. Capturas de tela (se aplicável)
4. Ambiente (versão do Python, bibliotecas, sistema operacional)

### Sugerindo Melhorias

Sugestões de melhorias são bem-vindas. Para sugerir:

1. Crie uma nova issue
2. Descreva sua sugestão em detalhes
3. Explique como a melhoria beneficiaria os usuários

### Enviando Pull Requests

1. Faça fork do repositório
2. Crie um branch para sua contribuição (`git checkout -b feature/sua-feature`)
3. Faça as alterações no código
4. Execute os testes, se disponíveis
5. Faça commit das suas alterações (`git commit -m 'Adiciona recurso X'`)
6. Faça push para o branch (`git push origin feature/sua-feature`)
7. Crie um Pull Request

## Diretrizes de Codificação

### Estilo de Código

- Siga a PEP 8 para estilo de código Python
- Use nomes de variáveis e funções descritivos
- Adicione comentários para explicar trechos complexos
- Documente funções usando docstrings

### Proteção de Dados (LGPD)

Ao contribuir com código que lida com dados pessoais:

- Nunca armazene mais dados do que o necessário
- Garanta que o consentimento seja obtido antes da coleta
- Implemente medidas para permitir que os usuários exerçam seus direitos
- Documente todos os fluxos de dados em comentários
- Teste cuidadosamente funcionalidades de exclusão de dados

### Testes

- Adicione testes para novos recursos quando possível
- Verifique se os testes existentes passam antes de enviar um PR

## Processo de Review

- Todos os PRs serão revisados por pelo menos um mantenedor
- Os revisores podem solicitar alterações antes do merge
- Os PRs devem passar nos testes automatizados, se disponíveis

## Setup de Desenvolvimento

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/ccb-alerta-bot.git
cd ccb-alerta-bot

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows

# Instale as dependências
pip install -r requirements.txt

# Configure um arquivo config.py com suas próprias credenciais para teste
```

---

*A Santa Paz de Deus!* 🙏
