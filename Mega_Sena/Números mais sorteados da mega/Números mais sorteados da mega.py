#!/usr/bin/env python3

# Importa as bibliotecas necessárias
from requests import get, exceptions
from bs4 import BeautifulSoup as sp
from operator import itemgetter
import pandas as pd
from tabulate import tabulate

# Define a URL do site com os resultados da Mega Sena
url = 'https://asloterias.com.br/lista-de-resultados-da-mega-sena'

# Dicionário para contar a frequência de cada dezena
mega_dezenas = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0, '8': 0,
                '9': 0, '10': 0, '11': 0, '12': 0, '13': 0, '14': 0, '15': 0,
                '16': 0, '17': 0, '18': 0, '19': 0, '20': 0, '21': 0, '22': 0,
                '23': 0, '24': 0, '25': 0, '26': 0, '27': 0, '28': 0, '29': 0,
                '30': 0, '31': 0, '32': 0, '33': 0, '34': 0, '35': 0, '36': 0,
                '37': 0, '38': 0, '39': 0, '40': 0, '41': 0, '42': 0, '43': 0,
                '44': 0, '45': 0, '46': 0, '47': 0, '48': 0, '49': 0, '50': 0,
                '51': 0, '52': 0, '53': 0, '54': 0, '55': 0, '56': 0, '57': 0,
                '58': 0, '59': 0, '60': 0}

try:
    # Tentativa de conexão com o site
    print('Conectando-se ao site "asloterias.com.br" ...')

    # Faz a requisição HTTP para obter o conteúdo do site
    with get(url, stream=True) as carregaurl:
        # Mensagem indicando que a conexão foi feita com sucesso
        print('Conexão feita com sucesso!\n\n')
        
        # Lista para armazenar as strings que contêm os resultados
        saida_colunas = []

        # Itera sobre as linhas do HTML para extrair as strings com os resultados
        for linhas_tr in sp(carregaurl.content, "lxml")\
                .findAll("div", class_="limpar_flutuacao"):
            # Adiciona as strings à lista
            saida_colunas.append(linhas_tr.previous_sibling)

except exceptions.HTTPError as erro:
    # Se ocorrer um erro de conexão HTTP, exibe uma mensagem de erro e encerra o programa
    exit(f'--- Erro {erro} na conexao HTTP com o site ---')

# Abre um arquivo para armazenar os resultados em um formato simples (CSV)
with open('todos_os_resultados.csv', 'w') as arquivo_com_resultados:

    # Limpa o conteúdo do arquivo (caso exista)
    arquivo_com_resultados.truncate(0)

    # Itera sobre os resultados extraídos
    for resultado in list(saida_colunas):
        # Extrai cada dezena dos resultados
        dez1 = int(resultado[17:19])
        dez2 = int(resultado[20:22])
        dez3 = int(resultado[23:25])
        dez4 = int(resultado[26:28])
        dez5 = int(resultado[29:31])
        dez6 = int(resultado[32:34])
        
        # Formata as dezenas em uma string
        dezenas = f'{dez1},{dez2},{dez3},{dez4},{dez5},{dez6}'

        # Escreve as dezenas no arquivo
        print(dezenas, file=arquivo_com_resultados)
        
        # Atualiza a contagem de frequência de cada dezena
        for dezena in dezenas.split(','):
            if dezena in mega_dezenas:
                mega_dezenas[dezena] += 1

# Cria um DataFrame a partir do dicionário de contagem das dezenas
df_mega_dezenas = pd.DataFrame(list(mega_dezenas.items()), columns=['Dezena', 'Frequencia'])

# Ordena o DataFrame pela frequência em ordem decrescente
df_mega_dezenas = df_mega_dezenas.sort_values(by='Frequencia', ascending=False)

# Exibe as 10 dezenas mais sorteadas na MegaSena de maneira mais amigável
print('--- As 10 dezenas mais (+) sorteadas na MegaSena até hoje ---\n')
print(tabulate(df_mega_dezenas.head(10), headers='keys', tablefmt='fancy_grid', showindex=False))

# Exibe as 10 dezenas menos sorteadas na MegaSena de maneira mais amigável
print('\n--- As 10 dezenas menos (-) sorteadas na MegaSena até hoje ---\n')
print(tabulate(df_mega_dezenas.tail(10), headers='keys', tablefmt='fancy_grid', showindex=False))

# Cria um DataFrame a partir do dicionário de contagem das dezenas
df_mega_dezenas = pd.DataFrame(list(mega_dezenas.items()), columns=['Dezena', 'Frequencia'])

# Ordena o DataFrame pela frequência em ordem decrescente
df_mega_dezenas = df_mega_dezenas.sort_values(by='Frequencia', ascending=False)

# Separa os DataFrames das 10 dezenas mais e menos frequentes
df_most_drawn = df_mega_dezenas.head(10)
df_least_drawn = df_mega_dezenas.tail(10)

# Cria um gráfico interativo para as 10 dezenas mais frequentes
fig_most = px.bar(df_most_drawn, x='Dezena', y='Frequencia', title='Top 10 Dezenas Mais Sorteadas na Mega Sena',
                  labels={'Frequencia': 'Frequência'})
fig_most.show()

# Cria um gráfico interativo para as 10 dezenas menos frequentes
fig_least = px.bar(df_least_drawn, x='Dezena', y='Frequencia', title='Top 10 Dezenas Menos Sorteadas na Mega Sena',
                   labels={'Frequencia': 'Frequência'})
fig_least.show()