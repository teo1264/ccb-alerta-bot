#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dados pré-definidos para o CCB Alerta Bot
BLOCO 1/4: Remoção do "Outro" e implementação de detecção inteligente
"""

import unicodedata
import re

# Lista de igrejas com códigos (mantida igual)
IGREJAS = [
    {"codigo": "ADM-MAUÁ", "nome": "PRÉDIO ADMINISTRAÇÃO"},
    {"codigo": "PIA", "nome": "PRÉDIO DA PIEDADE"},
    {"codigo": "BR21-0270", "nome": "CENTRO"},
    {"codigo": "BR21-0271", "nome": "JARDIM PRIMAVERA"},
    {"codigo": "BR21-0272", "nome": "JARDIM MIRANDA D'AVIZ"},
    {"codigo": "BR21-0273", "nome": "JARDIM SANTISTA"},
    {"codigo": "BR21-0274", "nome": "JARDIM SÔNIA MARIA"},
    {"codigo": "BR21-0275", "nome": "JARDIM ZAÍRA"},
    {"codigo": "BR21-0276", "nome": "PARQUE DAS AMÉRICAS"},
    {"codigo": "BR21-0277", "nome": "PARQUE SÃO VICENTE"},
    {"codigo": "BR21-0278", "nome": "VILA NOVA MAUÁ"},
    {"codigo": "BR21-0373", "nome": "JARDIM ORATÓRIO"},
    {"codigo": "BR21-0395", "nome": "JARDIM LUZITANO"},
    {"codigo": "BR21-0408", "nome": "VILA CARLINA"},
    {"codigo": "BR21-0448", "nome": "JARDIM ZAÍRA - GLEBA C"},
    {"codigo": "BR21-0472", "nome": "JARDIM ARACY"},
    {"codigo": "BR21-0511", "nome": "ESTRADA SAPOPEMBA - KM 11"},
    {"codigo": "BR21-0520", "nome": "VILA ASSIS BRASIL"},
    {"codigo": "BR21-0562", "nome": "CAPUAVA"},
    {"codigo": "BR21-0566", "nome": "JARDIM ALTO DA BOA VISTA"},
    {"codigo": "BR21-0573", "nome": "JARDIM BOM RECANTO"},
    {"codigo": "BR21-0574", "nome": "JARDIM BRASÍLIA"},
    {"codigo": "BR21-0589", "nome": "ALTO DO MACUCO"},
    {"codigo": "BR21-0591", "nome": "JARDIM GUAPITUBA"},
    {"codigo": "BR21-0616", "nome": "JARDIM ZAÍRA - GLEBA A"},
    {"codigo": "BR21-0653", "nome": "JARDIM ITAPARK VELHO"},
    {"codigo": "BR21-0668", "nome": "VILA MAGINI"},
    {"codigo": "BR21-0727", "nome": "VILA MERCEDES"},
    {"codigo": "BR21-0736", "nome": "JARDIM ESPERANÇA"},
    {"codigo": "BR21-0745", "nome": "JARDIM HÉLIDA"},
    {"codigo": "BR21-0746", "nome": "JARDIM COLÚMBIA"},
    {"codigo": "BR21-0751", "nome": "VILA VITÓRIA"},
    {"codigo": "BR21-0757", "nome": "JARDIM CRUZEIRO"},
    {"codigo": "BR21-0774", "nome": "JARDIM MAUÁ"},
    {"codigo": "BR21-0856", "nome": "JARDIM ZAÍRA - GLEBA D"},
    {"codigo": "BR21-0920", "nome": "CHÁCARA MARIA FRANCISCA"},
    {"codigo": "BR21-1082", "nome": "JARDIM ITAPARK NOVO"},
    {"codigo": "BR21-1108", "nome": "RECANTO VITAL BRASIL"}
]

# Lista de funções disponíveis - REMOVIDO "Outro"
FUNCOES = [
    "Encarregado da Manutenção",
    "Auxiliar da Escrita",
    "Cooperador",
    "Diácono",
    "Ancião"
]

def normalizar_texto(texto):
    """
    Normaliza texto removendo acentos, convertendo para minúscula e removendo espaços extras
    
    Args:
        texto (str): Texto a ser normalizado
        
    Returns:
        str: Texto normalizado
    """
    if not texto:
        return ""
    
    # Remove acentos
    texto_sem_acento = unicodedata.normalize('NFD', texto)
    texto_sem_acento = re.sub(r'[\u0300-\u036f]', '', texto_sem_acento)
    
    # Converte para minúscula e remove espaços extras
    return re.sub(r'\s+', ' ', texto_sem_acento.lower().strip())

def calcular_distancia_levenshtein(s1, s2):
    """
    Calcula a distância de Levenshtein entre duas strings
    
    Args:
        s1 (str): Primeira string
        s2 (str): Segunda string
        
    Returns:
        int: Distância de Levenshtein
    """
    if len(s1) < len(s2):
        return calcular_distancia_levenshtein(s2, s1)

    if len(s2) == 0:
        return len(s1)

    linha_anterior = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        linha_atual = [i + 1]
        for j, c2 in enumerate(s2):
            # Custos de inserção, deleção e substituição
            insercoes = linha_anterior[j + 1] + 1
            delecoes = linha_atual[j] + 1
            substituicoes = linha_anterior[j] + (c1 != c2)
            linha_atual.append(min(insercoes, delecoes, substituicoes))
        linha_anterior = linha_atual
    
    return linha_anterior[-1]

def calcular_similaridade(s1, s2):
    """
    Calcula a similaridade entre duas strings (0.0 a 1.0)
    
    Args:
        s1 (str): Primeira string
        s2 (str): Segunda string
        
    Returns:
        float: Índice de similaridade (1.0 = idênticas, 0.0 = completamente diferentes)
    """
    if not s1 or not s2:
        return 0.0
    
    distancia = calcular_distancia_levenshtein(s1, s2)
    tamanho_maximo = max(len(s1), len(s2))
    
    if tamanho_maximo == 0:
        return 1.0
    
    return 1.0 - (distancia / tamanho_maximo)

def detectar_funcao_similar(funcao_digitada):
    """
    Detecta se a função digitada é similar a alguma função existente nos botões
    
    Args:
        funcao_digitada (str): Função digitada pelo usuário
        
    Returns:
        tuple: (bool, str) - (encontrou_similar, funcao_oficial)
                - Se encontrou: (True, "Nome da Função Oficial")
                - Se não encontrou: (False, "")
    """
    if not funcao_digitada or not funcao_digitada.strip():
        return False, ""
    
    funcao_normalizada = normalizar_texto(funcao_digitada)
    
    # Verificar cada função da lista oficial
    for funcao_oficial in FUNCOES:
        funcao_oficial_normalizada = normalizar_texto(funcao_oficial)
        
        # Comparação exata (após normalização)
        if funcao_normalizada == funcao_oficial_normalizada:
            return True, funcao_oficial
        
        # Comparação por similaridade (mínimo 85% de similaridade)
        similaridade = calcular_similaridade(funcao_normalizada, funcao_oficial_normalizada)
        if similaridade >= 0.85:
            return True, funcao_oficial
    
    return False, ""

# Agrupar igrejas por blocos para menu paginado (mantida igual)
def agrupar_igrejas(tamanho_pagina=8):
    """
    Agrupa a lista de igrejas em blocos para exibição no menu paginado
    
    Args:
        tamanho_pagina (int): Quantidade de igrejas por página
        
    Returns:
        list: Lista de listas com as igrejas agrupadas por páginas
    """
    paginas = []
    for i in range(0, len(IGREJAS), tamanho_pagina):
        paginas.append(IGREJAS[i:i + tamanho_pagina])
    return paginas

# Obter igreja pelo código (mantida igual)
def obter_igreja_por_codigo(codigo):
    """
    Retorna os dados da igreja pelo código
    
    Args:
        codigo (str): Código da igreja
        
    Returns:
        dict ou None: Dados da igreja ou None se não encontrada
    """
    codigo_normalizado = codigo.strip().upper().replace(" ", "")
    for igreja in IGREJAS:
        if igreja["codigo"].upper().replace(" ", "") == codigo_normalizado:
            return igreja
    return None

# Agrupar funções por blocos para menu (mantida igual)
def agrupar_funcoes(tamanho_pagina=3):
    """
    Agrupa a lista de funções em blocos para exibição no menu
    
    Args:
        tamanho_pagina (int): Quantidade de funções por página
        
    Returns:
        list: Lista de listas com as funções agrupadas por páginas
    """
    paginas = []
    for i in range(0, len(FUNCOES), tamanho_pagina):
        paginas.append(FUNCOES[i:i + tamanho_pagina])
    return paginas
