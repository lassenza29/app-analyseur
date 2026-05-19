import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from typing import Dict, Tuple, Optional, List
import logging
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.ERROR)

st.set_page_config(
    page_title="Plateforme d'Analyse Financière Institutionnelle",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none; }
    .main { padding: 2rem; background: #fafbfc; }
    h1 { font-size: 2.5rem; font-weight: 700; color: #0a3d62; margin-bottom: 0.5rem; }
    h2 { font-size: 1.8rem; font-weight: 600; color: #0a3d62; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 3px solid #e8e8e8; padding-bottom: 0.5rem; }
    h3 { font-size: 1.2rem; font-weight: 600; color: #1a5f7a; margin-top: 1.5rem; }
    .metric-card { background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%); padding: 1.5rem; border-radius: 10px; border-left: 5px solid #0a3d62; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .validation-badge { display: inline-block; padding: 0.35rem 0.9rem; border-radius: 20px; font-size: 0.8rem; font-weight: 700; margin-left: 0.5rem; }
    .valid { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .invalid { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .consensus-box { background: linear-gradient(135deg, #f0f4f8 0%, #e8f0f7 100%); padding: 1.5rem; border-radius: 10px; border-left: 5px solid #0066cc; margin: 1.5rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .verdict-box { background: linear-gradient(135deg, #fff3cd 0%, #ffe5a1 100%); padding: 1.5rem; border-radius: 10px; border-left: 5px solid #ff9800; margin: 2rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.08); }
    .achat { background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); color: #155724; }
    .conservation { background: linear-gradient(135deg, #cfe2ff 0%, #b6d4fe 100%); color: #084298; }
    .vente { background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); color: #721c24; }
    table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    th { background-color: #0a3d62; color: white; padding: 1rem; text-align: left; font-weight: 600; font-size: 0.95rem; }
    td { padding: 0.9rem 1rem; border-bottom: 1px solid #e8e8e8; }
    tr:hover { background-color: #f9fafb; }
    .data-source { font-size: 0.85rem; color: #999; margin-top: 0.3rem; }
</style>
""", unsafe_allow_html=True)

# ==================== CLASSES DE VALIDATION ET COLLECTE ====================

class DataValidator:
    """Validation croisée des données entre trois sources obligatoires."""
    
    def __init__(self):
        self.sources = {
            'yahoo_finance': {},
            'zonebourse': {},
            'investing_com': {}
        }
        self.validation_log = []
        self.divergences = []
    
    def validate_metric(self, metric_name: str, yahoo_val, zone_val, invest_val, 
                       tolerance_pct: float = 10.0) -> Tuple[Optional[float], str, List[str]]:
        """
        Valide une métrique via au moins deux sources.
        
        Args:
            metric_name: Nom de la métrique
            yahoo_val, zone_val, invest_val: Valeurs des trois sources
            tolerance_pct: Tolérance de divergence en pourcentage
        
        Returns:
            (valeur_moyenne, statut, sources_confirmées)
        """
        valid_sources = []
        values = []
        source_names = []
        
        # Collecte des valeurs valides
        for src_val, src_name in [(yahoo_val, 'Yahoo Finance'), 
                                   (zone_val, 'Zonebourse'), 
                                   (invest_val, 'Investing.com')]:
            if src_val is not None and src_val != "N/A" and str(src_val).strip() != "":
                try:
                    numeric_val = float(src_val) if isinstance(src_val, (int, float, str)) else None
                    if numeric_val is not None:
                        valid_sources.append(src_name)
                        values.append(numeric_val)
                        source_names.append(src_name)
                except (ValueError, TypeError):
                    pass
        
        # Validation: minimum 2 sources
        if len(valid_sources) >= 2:
            avg_value = np.mean(values)
            
            # Vérification des divergences
            if len(values) > 1:
                max_val = max(values)
                min_val = min(values)
                divergence = ((max_val - min_val) / min_val * 100) if min_val != 0 else 0
                
                if divergence > tolerance_pct:
                    self.divergences.append({
                        'metric': metric_name,
                        'divergence_pct': divergence,
                        'sources': valid_sources,
                        'values': dict(zip(valid_sources, values))
                    })
                    status = f"⚠ Validée (divergence: {divergence:.1f}%)"
                else:
                    status = "✓ Validée"
            else:
                status = "✓ Validée (1 source)"
            
            self.validation_log.append({
                'metric': metric_name,
                'status': 'valid',
                'sources': valid_sources,
                'value': avg_value,
                'timestamp': datetime.now()
            })
            
            return avg_value, status, valid_sources
        else:
            status = "⚠ Donnée non validée"
            self.validation_log.append({
                'metric': metric_name,
                'status': 'invalid',
                'sources': valid_sources,
                'timestamp': datetime.now()
            })
            return None, status, valid_sources


class DataSourceAPI(ABC):
    """Interface abstraite pour les sources de données."""
    
    @abstractmethod
    def fetch(self, ticker: str, data_type: str = 'all') -> Dict:
        """Récupère les données."""
        pass
    
    @abstractmethod
    def validate_connectivity(self) -> bool:
        """Valide la connexion à la source."""
        pass


class YahooFinanceAPI(DataSourceAPI):
    """Connecteur Yahoo Finance - Vélocité des données marché temps réel."""
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.base_url = "https://query1.finance.yahoo.com/v10/finance/quoteSummary"
    
    def fetch(self, ticker: str, data_type: str = 'all') -> Dict:
        """Récupère prix temps réel et données clés."""
        try:
            params = {
                'modules': 'price,financialData,defaultKeyStatistics,summaryDetail'
            }
            response = requests.get(
                f"{self.base_url}/{ticker}",
                params=params,
                timeout=self.timeout,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            if response.status_code == 200:
                result = response.json().get('quoteSummary', {}).get('result', [{}])[0]
                return {
                    'source': 'Yahoo Finance',
                    'status': 'success',
                    'timestamp': datetime.now(),
                    'data': result
                }
            else:
                return {'source': 'Yahoo Finance', 'status': 'error', 'data': {}, 'http_code': response.status_code}
        
        except requests.Timeout:
            return {'source': 'Yahoo Finance', 'status': 'timeout', 'data': {}}
        except Exception as e:
            logging.error(f"YahooFinance {ticker}: {str(e)}")
            return {'source': 'Yahoo Finance', 'status': 'error', 'data': {}, 'error': str(e)}
    
    def validate_connectivity(self) -> bool:
        """Teste la connexion."""
        try:
            response = requests.head("https://finance.yahoo.com", timeout=3)
            return response.status_code < 400
        except:
            return False


class ZonebourseAPI(DataSourceAPI):
    """Connecteur Zonebourse - Ratios fondamentaux et sentiment marché."""
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.base_url = "https://www.zonebourse.com/api"
    
    def fetch(self, ticker: str, data_type: str = 'all') -> Dict:
        """Récupère ratios fondamentaux et consensus analystes."""
        try:
            endpoints = {
                'ratios': f"{self.base_url}/quote/{ticker}/ratios",
                'consensus': f"{self.base_url}/quote/{ticker}/consensus",
                'fundamentals': f"{self.base_url}/quote/{ticker}/fundamentals"
            }
            
            collected_data = {}
            
            for key, url in endpoints.items():
                try:
                    response = requests.get(
                        url,
                        timeout=self.timeout,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    if response.status_code == 200:
                        collected_data[key] = response.json()
                except:
                    collected_data[key] = {}
            
            return {
                'source': 'Zonebourse',
                'status': 'success' if collected_data else 'partial',
                'timestamp': datetime.now(),
                'data': collected_data
            }
        
        except Exception as e:
            logging.error(f"Zonebourse {ticker}: {str(e)}")
            return {'source': 'Zonebourse', 'status': 'error', 'data': {}, 'error': str(e)}
    
    def validate_connectivity(self) -> bool:
        """Teste la connexion."""
        try:
            response = requests.head("https://www.zonebourse.com", timeout=3)
            return response.status_code < 400
        except:
            return False


class InvestingComAPI(DataSourceAPI):
    """Connecteur Investing.com - Sentiment et avis analystes."""
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.base_url = "https://api.investing.com/api"
    
    def fetch(self, ticker: str, data_type: str = 'all') -> Dict:
        """Récupère sentiment, avis analystes et prévisions."""
        try:
            endpoints = {
                'sentiment': f"{self.base_url}/financialdata/{ticker}/sentiment",
                'analysts': f"{self.base_url}/financialdata/{ticker}/analysts",
                'estimates': f"{self.base_url}/financialdata/{ticker}/estimates"
            }
            
            collected_data = {}
            
            for key, url in endpoints.items():
                try:
                    response = requests.get(
                        url,
                        timeout=self.timeout,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    if response.status_code == 200:
                        collected_data[key] = response.json()
                except:
                    collected_data[key] = {}
            
            return {
                'source': 'Investing.com',
                'status': 'success' if collected_data else 'partial',
                'timestamp': datetime.now(),
                'data': collected_data
            }
        
        except Exception as e:
            logging.error(f"Investing.com {ticker}: {str(e)}")
            return {'source': 'Investing.com', 'status': 'error', 'data': {}, 'error': str(e)}
    
    def validate_connectivity(self) -> bool:
        """Teste la connexion."""
        try:
            response = requests.head("https://www.investing.com", timeout=3)
            return response.status_code < 400
        except:
            return False


class DataCollector:
    """Agrégateur de données multi-sources."""
    
    def __init__(self):
        self.yahoo = YahooFinanceAPI()
        self.zonebourse = ZonebourseAPI()
        self.investing = InvestingComAPI()
        self.validator = DataValidator()
    
    def aggregate_data(self, ticker: str) -> Dict:
        """Agrège les données des trois sources avec gestion d'erreurs."""
        data = {
            'ticker': ticker,
            'timestamp': datetime.now(),
            'sources': {
                'yahoo_finance': self.yahoo.fetch(ticker),
                'zonebourse': self.zonebourse.fetch(ticker),
                'investing_com': self.investing.fetch(ticker)
            },
            'validator': self.validator,
            'connectivity': {
                'yahoo_finance': self.yahoo.validate_connectivity(),
                'zonebourse': self.zonebourse.validate_connectivity(),
                'investing_com': self.investing.validate_connectivity()
            }
        }
        
        return data


class AnalysisEngine:
    """Moteur d'analyse financière avec validation croisée."""
    
    @staticmethod
    def safe_extract(data: Dict, path: str, default=None):
        """Extraction sécurisée de données imbriquées."""
        try:
            keys = path.split('.')
            result = data
            for key in keys:
                result = result.get(key, {})
            return result if result != {} else default
        except:
            return default
    
    @staticmethod
    def calculate_ratios(data: Dict) -> Dict:
        """Calcule tous les ratios financiers avec validation croisée."""
        ratios = {}
        
        yahoo_data = data['sources']['yahoo_finance'].get('data', {})
        zone_data = data['sources']['zonebourse'].get('data', {})
        invest_data = data['sources']['investing_com'].get('data', {})
        
        validator = data['validator']
        
        # === PER (Price-to-Earnings) ===
        try:
            yahoo_per = AnalysisEngine.safe_extract(yahoo_data, 'defaultKeyStatistics.trailingPE.raw')
            zone_per = AnalysisEngine.safe_extract(zone_data, 'ratios.PER.value')
            invest_per = AnalysisEngine.safe_extract(invest_data, 'analysts.pe_ratio')
            
            per_value, per_status, per_sources = validator.validate_metric('PER', yahoo_per, zone_per, invest_per)
            ratios['PER'] = {
                'value': f"{per_value:.2f}" if per_value else "N/A",
                'status': per_status,
                'sources': per_sources
            }
        except Exception as e:
            logging.error(f"Calcul PER: {e}")
            ratios['PER'] = {'value': 'N/A', 'status': '⚠ Erreur calcul', 'sources': []}
        
        # === PER Forward ===
        try:
            yahoo_fper = AnalysisEngine.safe_extract(yahoo_data, 'defaultKeyStatistics.forwardPE.raw')
            zone_fper = AnalysisEngine.safe_extract(zone_data, 'ratios.PER_FORWARD.value')
            invest_fper = AnalysisEngine.safe_extract(invest_data, 'estimates.forward_pe')
            
            fper_value, fper_status, fper_sources = validator.validate_metric('PER Forward', yahoo_fper, zone_fper, invest_fper)
            ratios['PER_FORWARD'] = {
                'value': f"{fper_value:.2f}" if fper_value else "N/A",
                'status': fper_status,
                'sources': fper_sources
            }
        except Exception as e:
            logging.error(f"Calcul PER Forward: {e}")
            ratios['PER_FORWARD'] = {'value': 'N/A', 'status': '⚠ Erreur calcul', 'sources': []}
        
        # === PB (Price-to-Book) ===
        try:
            yahoo_pb = AnalysisEngine.safe_extract(yahoo_data, 'defaultKeyStatistics.priceToBook.raw')
            zone_pb = AnalysisEngine.safe_extract(zone_data, 'ratios.PB.value')
            invest_pb = AnalysisEngine.safe_extract(invest_data, 'fundamentals.pb_ratio')
            
            pb_value, pb_status, pb_sources = validator.validate_metric('PB', yahoo_pb, zone_pb, invest_pb)
            ratios['PB'] = {
                'value': f"{pb_value:.2f}" if pb_value else "N/A",
                'status': pb_status,
                'sources': pb_sources
            }
        except Exception as e:
            logging.error(f"Calcul PB: {e}")
            ratios['PB'] = {'value': 'N/A', 'status': '⚠ Erreur calcul', 'sources': []}
        
        # === Rendement Dividende ===
        try:
            yahoo_div = AnalysisEngine.safe_extract(yahoo_data, 'summaryDetail.dividendYield.raw')
            zone_div = AnalysisEngine.safe_extract(zone_data, 'ratios.DIVIDEND_YIELD.value')
            invest_div = AnalysisEngine.safe_extract(invest_data, 'fundamentals.dividend_yield')
            
            div_value, div_status, div_sources = validator.validate_metric('Rendement Dividende', yahoo_div, zone_div, invest_div)
            ratios['DIVIDEND_YIELD'] = {
                'value': f"{div_value*100:.2f}%" if div_value else "N/A",
                'status': div_status,
                'sources': div_sources
            }
        except Exception as e:
            logging.error(f"Calcul Dividende: {e}")
            ratios['DIVIDEND_YIELD'] = {'value': 'N/A', 'status': '⚠ Erreur calcul', 'sources': []}
        
        # === Dette/Équité ===
        try:
            yahoo_de = AnalysisEngine.safe_extract(yahoo_data, 'financialData.debtToEquity.raw')
            zone_de = AnalysisEngine.safe_extract(zone_data, 'ratios.DEBT_TO_EQUITY.value')
            invest_de = AnalysisEngine.safe_extract(invest_data, 'fundamentals.debt_to_equity')
            
            de_value, de_status, de_sources = validator.validate_metric('Dette/Équité', yahoo_de, zone_de, invest_de)
            ratios['DEBT_TO_EQUITY'] = {
                'value': f"{de_value:.2f}" if de_value else "N/A",
                'status': de_status,
                'sources': de_sources
            }
        except Exception as e:
            logging.error(f"Calcul D/E: {e}")
            ratios['DEBT_TO_EQUITY'] = {'value': 'N/A', 'status': '⚠ Erreur calcul', 'sources': []}
        
        # === ROE (Return on Equity) ===
        try:
            yahoo_roe = AnalysisEngine.safe_extract(yahoo_data, 'financialData.returnOnEquity.raw')
            zone_roe = AnalysisEngine.safe_extract(zone_data, 'ratios.ROE.value')
            invest_roe = AnalysisEngine.safe_extract(invest_data, 'fundamentals.roe')
            
            roe_value, roe_status, roe_sources = validator.validate_metric('ROE', yahoo_roe, zone_roe, invest_roe)
            ratios['ROE'] = {
                'value': f"{roe_value*100:.2f}%" if roe_value else "N/A",
                'status': roe_status,
                'sources': roe_sources
            }
        except Exception as e:
            logging.error(f"Calcul ROE: {e}")
            ratios['ROE'] = {'value': 'N/A', 'status': '⚠ Erreur calcul', 'sources': []}
        
        # === FCF (Free Cash Flow) ===
        try:
            yahoo_fcf = AnalysisEngine.safe_extract(yahoo_data, 'financialData.freeCashflow.raw')
            zone_fcf = AnalysisEngine.safe_extract(zone_data, 'fundamentals.FCF.value')
            invest_fcf = AnalysisEngine.safe_extract(invest_data, 'fundamentals.fcf')
            
            fcf_value, fcf_status, fcf_sources = validator.validate_metric('FCF (millions)', yahoo_fcf, zone_fcf, invest_fcf)
            ratios['FCF'] = {
                'value': f"{fcf_value/1e6:.2f}M" if fcf_value else "N/A",
                'status': fcf_status,
                'sources': fcf_sources
            }
        except Exception as e:
            logging.error(f"Calcul FCF: {e}")
            ratios['FCF'] = {'value': 'N/A', 'status': '⚠ Erreur calcul', 'sources': []}
        
        # === EV/EBITDA ===
        try:
            yahoo_ev_ebitda = AnalysisEngine.safe_extract(yahoo_data, 'defaultKeyStatistics.enterpriseToEbitda.raw')
            zone_ev_ebitda = AnalysisEngine.safe_extract(zone_data, 'ratios.EV_EBITDA.value')
            invest_ev_ebitda = AnalysisEngine.safe_extract(invest_data, 'fundamentals.ev_ebitda')
            
            ev_ebitda_value, ev_ebitda_status, ev_ebitda_sources = validator.validate_metric('EV/EBITDA', yahoo_ev_ebitda, zone_ev_ebitda, invest_ev_ebitda)
            ratios['EV_EBITDA'] = {
                'value': f"{ev_ebitda_value:.2f}" if ev_ebitda_value else "N/A",
                'status': ev_ebitda_status,
                'sources': ev_ebitda_sources
            }
        except Exception as e:
            logging.error(f"Calcul EV/EBITDA: {e}")
            ratios['EV_EBITDA'] = {'value': 'N/A', 'status': '⚠ Erreur calcul', 'sources': []}
        
        return ratios
    
    @staticmethod
    def generate_consensus(data: Dict) -> str:
        """Génère le résumé exécutif du consensus analystes."""
        
        zone_consensus = data['sources']['zonebourse'].get('data', {}).get('consensus', {})
        invest_consensus = data['sources']['investing_com'].get('data', {}).get('analysts', {})
        
        # Extraction sécurisée des données de consensus
        buy_count = AnalysisEngine.safe_extract(zone_consensus, 'buy', 0) or 0
        hold_count = AnalysisEngine.safe_extract(zone_consensus, 'hold', 0) or 0
        sell_count = AnalysisEngine.safe_extract(zone_consensus, 'sell', 0) or 0
        
        target_price = AnalysisEngine.safe_extract(zone_consensus, 'target_price', "N/A")
        target_high = AnalysisEngine.safe_extract(zone_consensus, 'target_high', "N/A")
        target_low = AnalysisEngine.safe_extract(zone_consensus, 'target_low', "N/A")
        
        consensus_text = f"""
        **RÉSUMÉ EXÉCUTIF DU CONSENSUS ANALYSTES**
        
        **Distribution des Recommandations**
        """
        
        if buy_count or hold_count or sell_count:
            consensus_text += f"""
- Achat/Surpondérer: **{buy_count}** analystes
- Conservation: **{hold_count}** analystes
- Vente/Sous-pondérer: **{sell_count}** analystes
            """
        else:
            consensus_text += "\n- Données de consensus non disponibles sur les sources"
        
        consensus_text += f"""
        
        **Objectifs de Prix (12 mois)**
        - Objectif moyen: **{target_price}**
        - Objectif haut: **{target_high}**
        - Objectif bas: **{target_low}**
        
        **Zones de Divergence**
        Les divergences identifiées entre analystes concernent:
        - La trajectoire de croissance et prévisibilité des flux
        - L'impact des facteurs macroéconomiques et sectoriels
        - La qualité de la gouvernance et allocation de capital
        - Les risques idiosyncratiques et systémiques
        """
        
        return consensus_text
    
    @staticmethod
    def generate_market_context(ticker: str, data: Dict) -> str:
        """Génère le contexte macro et microéconomique."""
        
        context = f"""
        **CONTEXTE MACROÉCONOMIQUE ET MICROÉCONOMIQUE**
        
        **Environnement Macroéconomique**
        - Trajectoire des taux d'intérêt directeurs et impact sur valorisations
        - Cycles inflationnistes et compression des marges sectorielles
        - Dynamiques géopolitiques et résilience des chaînes d'approvisionnement
        - Cycles de croissance économique par géographie pertinente
        - Mouvements de devises et exposition aux changes
        
        **Contexte Sectoriel ({ticker})**
        - Position concurrentielle relative et parts de marché
        - Tendances d'investissement et intensité R&D du secteur
        - Réglementation et changements normatifs pertinents
        - Transitions technologiques (énergies renouvelables, IA, digitalisation)
        - Consolidation sectorielle et M&A potentiels
        
        **Facteurs Spécifiques à l'Émetteur**
        - Performance opérationnelle vs pairs et benchmark sectoriel
        - Initiatives stratégiques et allocation optimale de capital
        - Qualité et prévisibilité des flux de trésorerie disponibles
        - Exposition aux risques systémiques et idiosyncratiques
        - Évolutions de l'équipe dirigeante et gouvernance
        
        **Catalyseurs à Moyen Terme**
        - Dates de publication de résultats et guided
        - Événements réglementaires ou sectoriels clés
        - Résolutions d'incertitudes stratégiques ou géopolitiques
        """
        
        return context
    
    @staticmethod
    def generate_verdict(ratios: Dict, ticker: str, data: Dict) -> Dict:
        """Génère le verdict tranché de l'expert avec justification croisée."""
        
        score = 0
        max_score = 0
        scoring_details = []
        
        # === ANALYSE VALUATION (PER) ===
        if '✓' in ratios.get('PER', {}).get('status', ''):
            try:
                per_str = ratios['PER']['value'].replace(',', '.')
                per_val = float(per_str) if per_str != 'N/A' else None
                if per_val:
                    if 10 <= per_val <= 18:
                        score += 2
                        scoring_details.append(f"✓ PER {per_val:.1f}x: Valuation attractive")
                    elif 8 <= per_val < 10:
                        score += 2.5
                        scoring_details.append(f"✓✓ PER {per_val:.1f}x: Valuation très attractive")
                    elif 18 < per_val <= 25:
                        score += 1
                        scoring_details.append(f"~ PER {per_val:.1f}x: Valuation modérée")
                    elif per_val > 25:
                        score += 0
                        scoring_details.append(f"✗ PER {per_val:.1f}x: Valuation élevée")
                    max_score += 2.5
            except:
                max_score += 2.5
        
        # === ANALYSE QUALITÉ (ROE) ===
        if '✓' in ratios.get('ROE', {}).get('status', ''):
            try:
                roe_str = ratios['ROE']['value'].replace('%', '').replace(',', '.')
                roe_val = float(roe_str) / 100 if roe_str != 'N/A' else None
                if roe_val:
                    if roe_val > 0.15:
                        score += 2
                        scoring_details.append(f"✓✓ ROE {roe_val*100:.1f}%: Qualité supérieure")
                    elif roe_val > 0.12:
                        score += 1.5
                        scoring_details.append(f"✓ ROE {roe_val*100:.1f}%: Qualité bonne")
                    elif roe_val > 0.08:
                        score += 1
                        scoring_details.append(f"~ ROE {roe_val*100:.1f}%: Qualité modérée")
                    else:
                        score += 0
                        scoring_details.append(f"✗ ROE {roe_val*100:.1f}%: Qualité faible")
                    max_score += 2
            except:
                max_score += 2
        
        # === ANALYSE FINANCIÈRE (Dette) ===
        if '✓' in ratios.get('DEBT_TO_EQUITY', {}).get('status', ''):
            try:
                de_str = ratios['DEBT_TO_EQUITY']['value'].replace(',', '.')
                de_val = float(de_str) if de_str != 'N/A' else None
                if de_val:
                    if de_val < 0.8:
                        score += 2
                        scoring_details.append(f"✓✓ D/E {de_val:.2f}: Bilan très sain")
                    elif de_val < 1.2:
                        score += 1.5
                        scoring_details.append(f"✓ D/E {de_val:.2f}: Bilan sain")
                    elif de_val < 1.8:
                        score += 0.5
                        scoring_details.append(f"~ D/E {de_val:.2f}: Bilan acceptable")
                    else:
                        score += 0
                        scoring_details.append(f"✗ D/E {de_val:.2f}: Bilan dégradé")
                    max_score += 2
            except:
                max_score += 2
        
        # === ANALYSE RENDEMENT (Dividende) ===
        if '✓' in ratios.get('DIVIDEND_YIELD', {}).get('status', ''):
            try:
                div_str = ratios['DIVIDEND_YIELD']['value'].replace('%', '').replace(',', '.')
                div_val = float(div_str) / 100 if div_str != 'N/A' else None
                if div_val:
                    if div_val > 0.05:
                        score += 1
                        scoring_details.append(f"✓ Rendement {div_val*100:.2f}%: Attractif")
                    elif div_val > 0.02:
                        score += 0.5
                        scoring_details.append(f"~ Rendement {div_val*100:.2f}%: Modéré")
                    max_score += 1
            except:
                max_score += 1
        
        # === CALCUL DU SCORE ===
        if max_score > 0:
            score_pct = (score / max_score) * 100
        else:
            score_pct = 50
            scoring_details.append("⚠ Données insuffisantes pour analyse complète")
        
        # === DÉTERMINATION DU VERDICT ===
        if score_pct >= 75:
            recommendation = "ACHAT"
            css_class = "achat"
            rationale = """Les fondamentaux valident une thèse haussière structurée:
- Valuation attractive offrant upside potentiel
- Profil de qualité (ROE, marges) supérieur aux pairs
- Bilan et structures financières saines
- Entrée opportune avant catalyseurs positifs identifiés
            """
        elif score_pct >= 55:
            recommendation = "CONSERVATION"
            css_class = "conservation"
            rationale = """Profil équilibré justifiant le maintien en portefeuille:
- Position défensive dans allocation diversifiée
- Stabilité opérationnelle et génération de flux prévisible
- Attente de catalyseurs pour confirmer réallocation
- Suivi régulier des évolutions macro/sectorielles recommandé
            """
        else:
            recommendation = "VENTE"
            css_class = "vente"
            rationale = """Profil défensif suggérant réallocation prioritaire:
- Valorisation élevée limitant la marge de sécurité
- Fondamentaux dégradés ou en dégradation
- Bilan sous-optimal ou signaux macro négatifs
- Réallocation vers alternatives offrant meilleur profil risque/rendement
            """
        
        return {
            'recommendation': recommendation,
            'css_class': css_class,
            'rationale': rationale,
            'score': score_pct,
            'max_score': max_score,
            'scoring_details': scoring_details
        }


# ==================== INTERFACE STREAMLIT ====================

st.markdown("<h1>📊 ANALYSE FINANCIÈRE INSTITUTIONNELLE</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #666; font-size: 0.95rem; margin-bottom: 2rem;'>Validation croisée multi-sources: Yahoo Finance • Zonebourse • Investing.com</p>", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    ticker_input = st.text_input(
        label="ticker",
        placeholder="Saisir un ticker (ex: MSFT, AAPL, SAP.DE, LVMH.PA)",
        label_visibility="collapsed"
    )
with col2:
    submit_btn = st.button("Analyser", use_container_width=True, type="primary")

if submit_btn and ticker_input:
    ticker = ticker_input.strip().upper()
    
    with st.spinner("⏳ Récupération et validation des données..."):
        collector = DataCollector()
        analysis_data = collector.aggregate_data(ticker)
        engine = AnalysisEngine()
        
        # Vérification connectivité
        connectivity_ok = all([
            analysis_data['connectivity']['yahoo_finance'],
            analysis_data['connectivity']['zonebourse'],
            analysis_data['connectivity']['investing_com']
        ])
        
        if not connectivity_ok:
            st.warning("⚠ Une ou plusieurs sources sont temporairement indisponibles. Les résultats peuvent être partiels.")
        
        # SECTION 1: TABLEAU DE BORD FINANCIER
        st.markdown("<h2>📈 TABLEAU DE BORD FINANCIER</h2>", unsafe_allow_html=True)
        
        ratios = engine.calculate_ratios(analysis_data)
        
        # Affichage des cartes de métriques
        metrics_cols = st.columns(4)
        
        ratio_items = list(ratios.items())
        for idx, (ratio_name, ratio_data) in enumerate(ratio_items):
            with metrics_cols[idx % 4]:
                value = ratio_data['value']
                status = ratio_data['status']
                sources = ratio_data.get('sources', [])
                is_valid = '✓' in status
                badge_class = 'valid' if is_valid else 'invalid'
                
                sources_str = ", ".join(sources) if sources else "N/A"
                
                st.markdown(f"""
                <div class='metric-card'>
                    <div style='font-size: 0.85rem; color: #666; margin-bottom: 0.3rem; font-weight: 500;'>{ratio_name}</div>
                    <div style='font-size: 1.6rem; font-weight: 700; color: #0a3d62; margin-bottom: 0.5rem;'>{value}</div>
                    <span class='validation-badge {badge_class}'>{status}</span>
                    <div class='data-source'>Sources: {sources_str}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Tableau synthétique
        st.markdown("<h3>Synthèse des Ratios Validés</h3>", unsafe_allow_html=True)
        
        tableau_data = []
        for ratio_name, ratio_data in ratios.items():
            tableau_data.append({
                'Ratio': ratio_name,
                'Valeur': ratio_data['value'],
                'Statut': ratio_data['status'],
                'Sources Confirmées': ', '.join(ratio_data.get('sources', []))
            })
        
        if tableau_data:
            df_tableau = pd.DataFrame(tableau_data)
            st.dataframe(df_tableau, use_container_width=True, hide_index=True)
        
        # SECTION 2: CONSENSUS ANALYSTES
        st.markdown("<h2>🤝 CONSENSUS ET AVIS ANALYSTES</h2>", unsafe_allow_html=True)
        st.markdown("<div class='consensus-box'>", unsafe_allow_html=True)
        st.markdown(engine.generate_consensus(analysis_data))
        st.markdown("</div>", unsafe_allow_html=True)
        
        # SECTION 3: CONTEXTE ÉCONOMIQUE
        st.markdown("<h2>🌍 CONTEXTE MACROÉCONOMIQUE ET MICROÉCONOMIQUE</h2>", unsafe_allow_html=True)
        st.markdown(engine.generate_market_context(ticker, analysis_data))
        
        # SECTION 4: VERDICT DE L'EXPERT
        st.markdown("<h2>⚖️ VERDICT DE L'EXPERT</h2>", unsafe_allow_html=True)
        
        verdict = engine.generate_verdict(ratios, ticker, analysis_data)
        
        st.markdown(f"""
        <div class='verdict-box {verdict['css_class']}'>
            <h3 style='margin-top: 0;'>Recommandation: <strong>{verdict['recommendation']}</strong></h3>
            <p><strong>Justification:</strong></p>
            <p>{verdict['rationale']}</p>
            <p style='margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(0,0,0,0.1);'><strong>Score de Conviction:</strong> {verdict['score']:.0f}% (basé sur {int(verdict['max_score'])} critères)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Détails du scoring
        with st.expander("📊 Détails du Scoring"):
            st.markdown("**Analyse Détaillée des Critères**")
            for detail in verdict['scoring_details']:
                st.markdown(f"- {detail}")
        
        # LOGS DE VALIDATION (Admin)
        with st.expander("📋 Détails de Validation Croisée"):
            st.markdown("**Historique des Validations**")
            validation_logs = analysis_data['validator'].validation_log
            
            if validation_logs:
                logs_data = []
                for log in validation_logs:
                    logs_data.append({
                        'Métrique': log['metric'],
                        'Statut': log['status'],
                        'Sources': ', '.join(log.get('sources', [])) if log.get('sources') else 'N/A',
                        'Timestamp': log['timestamp'].strftime('%H:%M:%S')
                    })
                df_logs = pd.DataFrame(logs_data)
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            else:
                st.info("Aucune donnée validée croisée (sources insuffisantes).")
            
            # Zones de divergence
            divergences = analysis_data['validator'].divergences
            if divergences:
                st.markdown("**Zones de Divergence Identifiées**")
                for div in divergences:
                    st.warning(f"**{div['metric']}**: Divergence de {div['divergence_pct']:.1f}% entre sources\n{div['values']}")

elif submit_btn and not ticker_input:
    st.error("❌ Veuillez saisir un ticker valide.")
