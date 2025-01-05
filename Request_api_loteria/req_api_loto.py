import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import pandas as pd
from tabulate import tabulate
import sys
import os
from pathlib import Path
from datetime import datetime

class TipoLoteria(Enum):
    """
    Enum com os tipos de loteria disponíveis conforme documentação da API
    """
    DIA_DE_SORTE = "diadesorte"
    DUPLA_SENA = "duplasena"
    FEDERAL = "federal"
    LOTOFACIL = "lotofacil"
    LOTOMANIA = "lotomania"
    MAIS_MILIONARIA = "maismilionaria"
    MEGA_SENA = "megasena"
    QUINA = "quina"
    SUPER_SETE = "supersete"
    TIMEMANIA = "timemania"
    
    @classmethod
    def listar_opcoes(cls) -> List[str]:
        return [loteria.value for loteria in cls]
    
    @classmethod
    def validar_loteria(cls, valor: str) -> bool:
        return valor in cls.listar_opcoes()

class ResultadoLoteria:
    """
    Classe para representar um resultado de loteria com todos os campos possíveis
    """
    def __init__(self, dados: Dict[str, Any]):
        self.acumulou = dados.get('acumulou', False)
        self.concurso = dados.get('concurso', 0)
        self.data = self._parse_data(dados.get('data', ''))
        self.data_proximo_concurso = self._parse_data(dados.get('dataProximoConcurso', ''))
        self.dezenas = dados.get('dezenas', [])
        self.dezenas_ordem_sorteio = dados.get('dezenasOrdemSorteio', [])
        self.estados_premiados = dados.get('estadosPremiados', [])
        self.local = dados.get('local', '')
        self.local_ganhadores = dados.get('localGanhadores', [])
        self.loteria = dados.get('loteria', '')
        self.mes_sorte = dados.get('mesSorte', '')
        self.premiacoes = dados.get('premiacoes', [])
        self.valor_acumulado = dados.get('valorAcumulado', 0.0)
        self.valor_estimado_proximo_concurso = dados.get('valorEstimadoProximoConcurso', 0.0)
        
    def _parse_data(self, data_str: str) -> Optional[datetime]:
        """Converte string de data para objeto datetime"""
        if not data_str:
            return None
        try:
            return datetime.strptime(data_str, '%d/%m/%Y')
        except ValueError:
            return None
        
    def formatar_valor(self, valor: float) -> str:
        """Formata valor monetário"""
        return f"R$ {valor:,.2f}"
        
    def to_dict(self) -> Dict[str, Any]:
        """Converte o resultado para dicionário"""
        return {
            'concurso': self.concurso,
            'data': self.data.strftime('%d/%m/%Y') if self.data else 'N/A',
            'dezenas': ', '.join(self.dezenas),
            'acumulou': 'Sim' if self.acumulou else 'Não',
            'valor_acumulado': self.valor_acumulado,
            'proximo_concurso': self.data_proximo_concurso.strftime('%d/%m/%Y') if self.data_proximo_concurso else 'N/A',
            'valor_estimado_proximo': self.valor_estimado_proximo_concurso
        }

class LoteriasCaixaAPI:
    """
    Cliente para a API de Loterias da Caixa com tratamento completo da response
    """
    def __init__(self, timeout: int = 30):
        self.base_url = "https://loteriascaixa-api.herokuapp.com/api"
        self.timeout = timeout
        self.session = requests.Session()
        
    def _fazer_requisicao(self, endpoint: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/{endpoint}".rstrip('/')
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print(f"Timeout ao acessar {url}. Tempo limite: {self.timeout}s")
        except requests.exceptions.HTTPError as e:
            print(f"Erro HTTP {e.response.status_code} ao acessar {url}")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao fazer requisição para {url}: {e}")
        except json.JSONDecodeError:
            print(f"Erro ao decodificar resposta JSON de {url}")
        return None

    def obter_ultimo_resultado(self, loteria: TipoLoteria) -> Optional[ResultadoLoteria]:
        """Obtém o último resultado de uma loteria"""
        dados = self._fazer_requisicao(f"{loteria.value}/latest")
        return ResultadoLoteria(dados) if dados else None

    def obter_todos_resultados(self, loteria: TipoLoteria) -> List[ResultadoLoteria]:
        """Obtém todos os resultados de uma loteria"""
        dados = self._fazer_requisicao(f"{loteria.value}")
        return [ResultadoLoteria(resultado) for resultado in (dados or [])]

    def formatar_resultado(self, resultado: ResultadoLoteria) -> str:
        """
        Formata o resultado para exibição detalhada
        """
        if not resultado:
            return "Resultado não disponível"

        texto = f"""
=== Resultado {resultado.loteria.upper()} - Concurso {resultado.concurso} ===
Data: {resultado.data.strftime('%d/%m/%Y') if resultado.data else 'N/A'}
Local: {resultado.local}

Dezenas Sorteadas: {' - '.join(resultado.dezenas)}
Ordem do Sorteio: {' - '.join(resultado.dezenas_ordem_sorteio) if resultado.dezenas_ordem_sorteio else 'N/A'}

Status: {'ACUMULOU!' if resultado.acumulou else 'Houve Ganhador!'}
Valor Acumulado: {self.formatar_valor(resultado.valor_acumulado)}

Próximo Concurso: {resultado.data_proximo_concurso.strftime('%d/%m/%Y') if resultado.data_proximo_concurso else 'N/A'}
Valor Estimado: {self.formatar_valor(resultado.valor_estimado_proximo_concurso)}
""".strip()

        # Adiciona premiações
        if resultado.premiacoes:
            texto += "\n\nPremiações:"
            for premiacao in resultado.premiacoes:
                texto += f"\n{premiacao.get('descricao', 'N/A')}: "
                texto += f"{premiacao.get('ganhadores', 0)} ganhadores - "
                texto += self.formatar_valor(float(premiacao.get('valorPremio', 0)))

        # Adiciona locais dos ganhadores
        if resultado.local_ganhadores:
            texto += "\n\nGanhadores por Localidade:"
            for local in resultado.local_ganhadores:
                texto += f"\n{local.get('municipio', 'N/A')}/{local.get('uf', 'N/A')}: "
                texto += f"{local.get('ganhadores', 0)} ganhador(es)"

        # Adiciona campos específicos por tipo de loteria
        if resultado.mes_sorte:
            texto += f"\n\nMês da Sorte: {resultado.mes_sorte}"

        return texto

    def formatar_valor(self, valor: float) -> str:
        """Formata valor monetário"""
        return f"R$ {valor:,.2f}"

    def salvar_resultados_csv(self, loteria: TipoLoteria, resultados: List[ResultadoLoteria], 
                             pasta_destino: str = "resultados") -> None:
        """Salva os resultados em CSV"""
        if not resultados:
            print(f"Sem dados para salvar para {loteria.value}")
            return

        Path(pasta_destino).mkdir(parents=True, exist_ok=True)
        
        # Converte resultados para formato tabular
        dados = [resultado.to_dict() for resultado in resultados]
        df = pd.DataFrame(dados)
        
        arquivo = f"{pasta_destino}/{loteria.value}_resultados.csv"
        df.to_csv(arquivo, index=False, encoding='utf-8')
        print(f"Resultados salvos em: {arquivo}")

    def gerar_relatorio_estatistico(self, loteria: TipoLoteria, 
                                  resultados: List[ResultadoLoteria]) -> str:
        """
        Gera um relatório estatístico detalhado
        """
        if not resultados:
            return "Sem dados para análise"

        # Análise de dezenas
        todas_dezenas = []
        for resultado in resultados:
            todas_dezenas.extend([int(d) for d in resultado.dezenas])
        
        from collections import Counter
        frequencia = Counter(todas_dezenas)
        
        # Estatísticas gerais
        total_concursos = len(resultados)
        total_acumulados = sum(1 for r in resultados if r.acumulou)
        
        relatorio = f"""
=== Relatório Estatístico {loteria.value.upper()} ===
Total de Concursos Analisados: {total_concursos}
Total de Concursos Acumulados: {total_acumulados} ({(total_acumulados/total_concursos)*100:.1f}%)

Top 10 Dezenas Mais Sorteadas:
"""
        # Tabela de frequência
        dezenas_freq = sorted(frequencia.items(), key=lambda x: x[1], reverse=True)[:10]
        tabela = []
        for dezena, freq in dezenas_freq:
            porcentagem = (freq / total_concursos) * 100
            tabela.append([dezena, freq, f"{porcentagem:.1f}%"])
        
        relatorio += tabulate(tabela, 
                            headers=['Dezena', 'Frequência', 'Porcentagem'], 
                            tablefmt='grid')
        
        return relatorio

def menu_principal():
    """Menu interativo para o usuário"""
    api = LoteriasCaixaAPI()
    
    while True:
        print("\n=== Sistema de Consulta Loterias ===")
        print("1. Consultar último resultado")
        print("2. Obter todos os resultados")
        print("3. Gerar relatório estatístico")
        print("0. Sair")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "0":
            print("Encerrando programa...")
            break
            
        if opcao not in ["1", "2", "3"]:
            print("Opção inválida!")
            continue
        
        print("\nLoterias disponíveis:")
        for i, loteria in enumerate(TipoLoteria.listar_opcoes(), 1):
            print(f"{i}. {loteria}")
            
        try:
            escolha = int(input("\nEscolha o número da loteria: ")) - 1
            if escolha < 0 or escolha >= len(TipoLoteria.listar_opcoes()):
                print("Loteria inválida!")
                continue
                
            loteria = TipoLoteria(TipoLoteria.listar_opcoes()[escolha])
            
            if opcao == "1":
                print("\nObtendo último resultado...")
                resultado = api.obter_ultimo_resultado(loteria)
                if resultado:
                    print("\n" + api.formatar_resultado(resultado))
                else:
                    print("Não foi possível obter o resultado")
                
            elif opcao == "2":
                print("\nObtendo todos os resultados...")
                resultados = api.obter_todos_resultados(loteria)
                if resultados:
                    print(f"\nTotal de resultados encontrados: {len(resultados)}")
                    api.salvar_resultados_csv(loteria, resultados)
                else:
                    print("Não foi possível obter os resultados")
                
            elif opcao == "3":
                print("\nGerando relatório estatístico...")
                resultados = api.obter_todos_resultados(loteria)
                if resultados:
                    print(api.gerar_relatorio_estatistico(loteria, resultados))
                else:
                    print("Não foi possível gerar o relatório")
                
        except ValueError:
            print("Entrada inválida!")
        except Exception as e:
            print(f"Erro: {e}")
            
        input("\nPressione ENTER para continuar...")

if __name__ == "__main__":
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    menu_principal()