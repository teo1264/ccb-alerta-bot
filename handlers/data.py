#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dados pré-definidos para o CCB Alerta Bot
"""

# Lista de igrejas com códigos
IGREJAS = [
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

# Lista de funções disponíveis - Encarregado da Manutenção como primeira opção
FUNCOES = [
    "Encarregado da Manutenção",
    "Ancião",
    "Diácono",
    "Cooperador",
    "Auxiliar da Escrita",
    "Outro"
]

# Agrupar igrejas por blocos para menu paginado
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

# Obter igreja pelo código
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

# Agrupar funções por blocos para menu
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
