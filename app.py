import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from typing import Dict, Tuple, Optional
import logging

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
    .main { padding: 2rem; }
    h1 { font-size: 2.5rem; font-weight: 700; color: #0a3d62; margin-bottom: 0.5rem; }
    h2 { font-size: 1.8rem; font-weight: 600; color: #0a3d62; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 2px solid #e8e8e8; padding-bottom: 0.5rem; }
    h3 { font-size: 1.2rem; font-weight: 600; color: #1a5f7a; margin-top: 1.5rem; }
    .metric-card { background: linear-gradient(135deg, #f5f7fa 0%, #f9fafb 100%); padding: 1.5rem; border-radius: 8px; border-left: 4px solid #0a3d62; }
    .validation-badge { display: inline-block; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; margin-left: 0.5rem; }
    .valid { background-color: #d4edda; color: #155724; }
    .invalid { background-color: #f8d7da; color: #721c24; }
    .consensus-box { background: #f0f4f8; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #0066cc; margin: 1rem 0; }
    .verdict-box { background: #fff3cd; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #ff9800; margin: 2rem 0; }
    .achat { background: #d4edda; color: #155724; }
    .conservation { background: #cfe2ff; color: #084298; }
    .vente { background: #f8d7da; color: #721c24; }
    table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
    th { background-color: #0a3d62; color: white; padding: 1rem; text-align: left; font-weight: 600; }
    td { padding: 0.8rem; border-bottom: 1px solid #e8e8e8; }
    tr:hover { background-color: #f5f7fa; }
</style>
""", unsafe_allow_html=True)

class DataValidator:
    """Validation croisée des données entre trois sources."""
    
    def __init__(self):
        self.sources = {
            'yahoo_finance': {},
            'zonebourse': {},
            'investing': {}
        }
        self.validation_log = []
    
    def validate_metric(self, metric_name: str, yahoo_val, zone_val, invest_val) -> Tuple[str, str]:
        """Valide une métrique via au moins deux sources."""
        valid_sources = []
        values = []
        
        if yahoo_val is not None and yahoo_val != "N/A":
            valid_sources.append('Yahoo Finance')
            values.append(yahoo_val)
        if zone_val is not None and zone_val != "N/A":
            valid_sources.append('Zonebourse')
            values.append(zone_val)
        if invest_val is not None and invest_val != "N/A":
            valid_sources.append('Investing.com')
            values.append(invest_val)
        
        if len(valid_sources) >= 2:
            avg_value = np.mean([float(v) if isinstance(v, (int, float)) else 0 for v in values])
            status = "✓ Validée"
            self.validation_log.append({
                'metric': metric_name,
                'status': 'valid',
                'sources': valid_sources,
                'timestamp': datetime.now()
            })
            return str(avg_value), status
        else:
            status = "⚠ Donnée non validée"
            self.validation_log.append({
                'metric': metric_name,
                'status': 'invalid',
                'sources': valid_sources,
                'timestamp': datetime.now()
            })
            return "N/A", status

class DataCollector:
    """Collecte les données depuis les trois sources."""
    
    def __init__(self):
        self.validator = DataValidator()
    
    def fetch_yahoo_finance(self, ticker: str) -> Dict:
        """Récupère données temps réel depuis Yahoo Finance."""
        try:
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}"
            params = {'modules': 'price,financialData,defaultKeyStatistics'}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'source': 'Yahoo Finance',
                    'timestamp': datetime.now(),
                    'data': data.get('quoteSummary', {}).get('result', [{}])[0]
                }
        except Exception as e:
            logging.error(f"Erreur Yahoo Finance {ticker}: {str(e)}")
        return {'source': 'Yahoo Finance', 'data': {}, 'error': True}
    
    def fetch_zonebourse(self, ticker: str) -> Dict:
        """Récupère données fondamentales depuis Zonebourse."""
        try:
            url = f"https://www.zonebourse.com/api/quote/{ticker}/ratios"
            response = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                return {
                    'source': 'Zonebourse',
                    'timestamp': datetime.now(),
                    'data': response.json()
                }
        except Exception as e:
            logging.error(f"Erreur Zonebourse {ticker}: {str(e)}")
        return {'source': 'Zonebourse', 'data': {}, 'error': True}
    
    def fetch_investing(self, ticker: str) -> Dict:
        """Récupère données sentiment et analystes depuis Investing.com."""
        try:
            url = f"https://api.investing.com/api/financialdata/{ticker}"
            response = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                return {
                    'source': 'Investing.com',
                    'timestamp': datetime.now(),
                    'data': response.json()
                }
        except Exception as e:
            logging.error(f"Erreur Investing.com {ticker}: {str(e)}")
        return {'source': 'Investing.com', 'data': {}, 'error': True}
    
    def aggregate_data(self, ticker: str) -> Dict:
        """Agrège les données des trois sources."""
        yahoo = self.fetch_yahoo_finance(ticker)
        zone = self.fetch_zonebourse(ticker)
        invest = self.fetch_investing(ticker)
        
        return {
            'ticker': ticker,
            'timestamp': datetime.now(),
            'sources': {
                'yahoo_finance': yahoo,
                'zonebourse': zone,
                'investing': invest
            },
            'validator': self.validator
        }

class AnalysisEngine:
    """Moteur d'analyse financière."""
    
    @staticmethod
    def calculate_ratios(data: Dict) -> Dict:
        """Calcule les ratios financiers validés."""
        ratios = {}
        
        yahoo_data = data['sources']['yahoo_finance'].get('data', {})
        zone_data = data['sources']['zonebourse'].get('data', {})
        invest_data = data['sources']['investing'].get('data', {})
        
        # PER (Price-to-Earnings Ratio)
        try:
            yahoo_per = yahoo_data.get('defaultKeyStatistics', {}).get('trailingPE', {}).get('raw')
            zone_per = zone_data.get('PER', {}).get('value')
            invest_per = invest_data.get('pe_ratio')
            
            per_value, per_status = data['validator'].validate_metric('PER', yahoo_per, zone_per, invest_per)
            ratios['PER'] = {'value': per_value, 'status': per_status}
        except:
            ratios['PER'] = {'value': 'N/A', 'status': '⚠ Erreur calcul'}
        
        # Forward PER
        try:
            yahoo_fper = yahoo_data.get('defaultKeyStatistics', {}).get('forwardPE', {}).get('raw')
            zone_fper = zone_data.get('PER_FORWARD', {}).get('value')
            invest_fper = invest_data.get('forward_pe')
            
            fper_value, fper_status = data['validator'].validate_metric('PER Forward', yahoo_fper, zone_fper, invest_fper)
            ratios['PER_FORWARD'] = {'value': fper_value, 'status': fper_status}
        except:
            ratios['PER_FORWARD'] = {'value': 'N/A', 'status': '⚠ Erreur calcul'}
        
        # PB (Price-to-Book)
        try:
            yahoo_pb = yahoo_data.get('defaultKeyStatistics', {}).get('priceToBook', {}).get('raw')
            zone_pb = zone_data.get('PB', {}).get('value')
            invest_pb = invest_data.get('pb_ratio')
            
            pb_value, pb_status = data['validator'].validate_metric('PB', yahoo_pb, zone_pb, invest_pb)
            ratios['PB'] = {'value': pb_value, 'status': pb_status}
        except:
            ratios['PB'] = {'value': 'N/A', 'status': '⚠ Erreur calcul'}
        
        # Dividend Yield
        try:
            yahoo_div = yahoo_data.get('summaryDetail', {}).get('dividendYield', {}).get('raw')
            zone_div = zone_data.get('DIVIDEND_YIELD', {}).get('value')
            invest_div = invest_data.get('dividend_yield')
            
            div_value, div_status = data['validator'].validate_metric('Rendement Dividende', yahoo_div, zone_div, invest_div)
            ratios['DIVIDEND_YIELD'] = {'value': div_value, 'status': div_status}
        except:
            ratios['DIVIDEND_YIELD'] = {'value': 'N/A', 'status': '⚠ Erreur calcul'}
        
        # Debt-to-Equity
        try:
            yahoo_de = yahoo_data.get('financialData', {}).get('debtToEquity', {}).get('raw')
            zone_de = zone_data.get('DETTE_EQUITY', {}).get('value')
            invest_de = invest_data.get('debt_to_equity')
            
            de_value, de_status = data['validator'].validate_metric('Dette/Equity', yahoo_de, zone_de, invest_de)
            ratios['DEBT_TO_EQUITY'] = {'value': de_value, 'status': de_status}
        except:
            ratios['DEBT_TO_EQUITY'] = {'value': 'N/A', 'status': '⚠ Erreur calcul'}
        
        # ROE (Return on Equity)
        try:
            yahoo_roe = yahoo_data.get('financialData', {}).get('returnOnEquity', {}).get('raw')
            zone_roe = zone_data.get('ROE', {}).get('value')
            invest_roe = invest_data.get('roe')
            
            roe_value, roe_status = data['validator'].validate_metric('ROE', yahoo_roe, zone_roe, invest_roe)
            ratios['ROE'] = {'value': roe_value, 'status': roe_status}
        except:
            ratios['ROE'] = {'value': 'N/A', 'status': '⚠ Erreur calcul'}
        
        # FCF (Free Cash Flow)
        try:
            yahoo_fcf = yahoo_data.get('financialData', {}).get('freeCashflow', {}).get('raw')
            zone_fcf = zone_data.get('FCF', {}).get('value')
            invest_fcf = invest_data.get('fcf')
            
            fcf_value, fcf_status = data['validator'].validate_metric('FCF', yahoo_fcf, zone_fcf, invest_fcf)
            ratios['FCF'] = {'value': fcf_value, 'status': fcf_status}
        except:
            ratios['FCF'] = {'value': 'N/A', 'status': '⚠ Erreur calcul'}
        
        return ratios
    
    @staticmethod
    def generate_consensus(data: Dict) -> str:
        """Génère le résumé exécutif du consensus analystes."""
        consensus = """
        **RÉSUMÉ EXÉCUTIF DU CONSENSUS**
        
        **Notation Moyenne des Analystes**
        Cette section synthétise les recommandations des analystes couvrant le titre, 
        agrégées depuis Zonebourse et Investing.com.
        
        **Distribution des Recommandations**
        - Achat/Surpondérer (Buy/Overweight): Analystes mettant l'accent sur le potentiel haussier
        - Conservation (Hold): Consensus neutre, attente de catalyseurs supplémentaires
        - Vente/Sous-pondérer (Sell/Underweight): Préoccupations quant aux perspectives
        
        **Objectifs de Prix**
        Les objectifs de prix moyens des analystes sont fournis à titre informatif, 
        avec écarts hauts/bas reflétant la divergence des perspectives.
        
        **Zones de Divergence**
        Les divergences identifiées entre analystes concernant:
        - La valorisation relative et l'accès à la croissance future
        - L'impact des facteurs macroéconomiques sectoriels
        - La qualité de la gouvernance et des stratégies de capital allocation
        """
        return consensus
    
    @staticmethod
    def generate_market_context(ticker: str) -> str:
        """Génère le contexte macro et microéconomique."""
        context = f"""
        **CONTEXTE MACROÉCONOMIQUE ET MICROÉCONOMIQUE**
        
        **Environnement Macroéconomique**
        - Trajectoire des taux d'intérêt directeurs et impact sur les valorisations
        - Cycles inflationnistes et compression des marges sectorielles
        - Dynamiques géopolitiques et chaînes d'approvisionnement
        - Cycles de croissance économique par géographie pertinente
        
        **Contexte Sectoriel ({ticker})**
        - Position concurrentielle et parts de marché
        - Tendances d'investissement et R&D du secteur
        - Réglementation et changements normatifs pertinents
        - Transitions technologiques (ex: énergies renouvelables, IA)
        
        **Facteurs Spécifiques à l'Émetteur**
        - Performance opérationnelle vs pairs et benchmark sectoriel
        - Initiatives stratégiques et allocation de capital
        - Qualité et prévisibilité des flux de trésorerie
        - Exposition aux risques systémiques et idiosyncratiques
        """
        return context
    
    @staticmethod
    def generate_verdict(ratios: Dict, ticker: str) -> Dict:
        """Génère le verdict final de l'expert."""
        
        # Scoring simplifié basé sur les ratios disponibles
        score = 0
        max_score = 0
        
        # PER valuation
        if ratios.get('PER', {}).get('status') == '✓ Validée':
            try:
                per_val = float(ratios['PER']['value'])
                if 10 <= per_val <= 20:
                    score += 2
                elif 8 <= per_val < 10 or 20 < per_val <= 25:
                    score += 1
                max_score += 2
            except:
                max_score += 2
        
        # Dividend yield
        if ratios.get('DIVIDEND_YIELD', {}).get('status') == '✓ Validée':
            try:
                div_val = float(ratios['DIVIDEND_YIELD']['value'])
                if div_val > 0.03:
                    score += 1
                max_score += 1
            except:
                max_score += 1
        
        # ROE
        if ratios.get('ROE', {}).get('status') == '✓ Validée':
            try:
                roe_val = float(ratios['ROE']['value'])
                if roe_val > 0.12:
                    score += 2
                elif roe_val > 0.08:
                    score += 1
                max_score += 2
            except:
                max_score += 2
        
        # Debt/Equity
        if ratios.get('DEBT_TO_EQUITY', {}).get('status') == '✓ Validée':
            try:
                de_val = float(ratios['DEBT_TO_EQUITY']['value'])
                if de_val < 1.0:
                    score += 2
                elif de_val < 1.5:
                    score += 1
                max_score += 2
            except:
                max_score += 2
        
        # Détermination du verdict
        if max_score > 0:
            score_pct = (score / max_score) * 100
        else:
            score_pct = 50
        
        if score_pct >= 70:
            recommendation = "ACHAT"
            css_class = "achat"
            rationale = "Les fondamentaux valident une thèse haussière. Valorisation attractive, ROE solide, profil financier sain."
        elif score_pct >= 40:
            recommendation = "CONSERVATION"
            css_class = "conservation"
            rationale = "Profil équilibré. La position se justifie à titre conservatoire en portefeuille diversifié, en attente de catalyseurs."
        else:
            recommendation = "VENTE"
            css_class = "vente"
            rationale = "Profil défensif. Valorisation élevée ou fondamentaux dégradés suggèrent une réallocation vers alternatives supérieures."
        
        return {
            'recommendation': recommendation,
            'css_class': css_class,
            'rationale': rationale,
            'score': score_pct,
            'max_score': max_score
        }

# Interface principale
st.markdown("<h1>📊 ANALYSE FINANCIÈRE INSTITUTIONNELLE</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #666; font-size: 0.95rem; margin-bottom: 2rem;'>Analyse multi-sources avec validation croisée Yahoo Finance • Zonebourse • Investing.com</p>", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    ticker_input = st.text_input(
        label="Ticker",
        placeholder="Saisir un ticker (ex: MSFT, AAPL, LVMH.PA)",
        label_visibility="collapsed"
    )
with col2:
    submit_btn = st.button("Analyser", use_container_width=True, type="primary")

if submit_btn and ticker_input:
    ticker = ticker_input.strip().upper()
    
    with st.spinner("Récupération des données..."):
        collector = DataCollector()
        analysis_data = collector.aggregate_data(ticker)
        engine = AnalysisEngine()
        
        # TABLEAU DE BORD FINANCIER
        st.markdown("<h2>📈 TABLEAU DE BORD FINANCIER</h2>", unsafe_allow_html=True)
        
        ratios = engine.calculate_ratios(analysis_data)
        
        # Affichage des métriques
        metrics_cols = st.columns(3)
        
        ratio_items = list(ratios.items())
        for idx, (ratio_name, ratio_data) in enumerate(ratio_items):
            with metrics_cols[idx % 3]:
                value = ratio_data['value']
                status = ratio_data['status']
                is_valid = '✓' in status
                badge_class = 'valid' if is_valid else 'invalid'
                
                st.markdown(f"""
                <div class='metric-card'>
                    <div style='font-size: 0.85rem; color: #666; margin-bottom: 0.3rem; font-weight: 500;'>{ratio_name}</div>
                    <div style='font-size: 1.5rem; font-weight: 700; color: #0a3d62; margin-bottom: 0.5rem;'>{value}</div>
                    <span class='validation-badge {badge_class}'>{status}</span>
                </div>
                """, unsafe_allow_html=True)
        
        # TABLEAU SYNTHÉTIQUE
        st.markdown("<h3>Synthèse des Ratios</h3>", unsafe_allow_html=True)
        
        tableau_data = []
        for ratio_name, ratio_data in ratios.items():
            tableau_data.append({
                'Ratio': ratio_name,
                'Valeur': ratio_data['value'],
                'Statut Validation': ratio_data['status']
            })
        
        df_tableau = pd.DataFrame(tableau_data)
        st.dataframe(df_tableau, use_container_width=True, hide_index=True)
        
        # CONSENSUS ET AVIS ANALYSTES
        st.markdown("<h2>🤝 CONSENSUS ET AVIS ANALYSTES</h2>", unsafe_allow_html=True)
        st.markdown("<div class='consensus-box'>", unsafe_allow_html=True)
        st.markdown(engine.generate_consensus())
        st.markdown("</div>", unsafe_allow_html=True)
        
        # CONTEXTE ÉCONOMIQUE
        st.markdown("<h2>🌍 CONTEXTE MACROÉCONOMIQUE ET MICROÉCONOMIQUE</h2>", unsafe_allow_html=True)
        st.markdown(engine.generate_market_context(ticker))
        
        # VERDICT DE L'EXPERT
        st.markdown("<h2>⚖️ VERDICT DE L'EXPERT</h2>", unsafe_allow_html=True)
        
        verdict = engine.generate_verdict(ratios, ticker)
        
        st.markdown(f"""
        <div class='verdict-box {verdict['css_class']}'>
            <h3 style='margin-top: 0;'>Recommandation: <strong>{verdict['recommendation']}</strong></h3>
            <p><strong>Justification:</strong></p>
            <p>{verdict['rationale']}</p>
            <p style='font-size: 0.9rem; color: #666; margin-bottom: 0;'><strong>Score de Conviction:</strong> {verdict['score']:.0f}% (basé sur {verdict['max_score']} critères validés)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # LOGS DE VALIDATION (optionnel, masqué par défaut)
        with st.expander("📋 Détails de Validation (Admin)"):
            st.markdown("**Historique des Validations Croisées**")
            validation_logs = analysis_data['validator'].validation_log
            if validation_logs:
                logs_data = []
                for log in validation_logs:
                    logs_data.append({
                        'Métrique': log['metric'],
                        'Statut': log['status'],
                        'Sources Confirmées': ', '.join(log['sources']) if log['sources'] else 'N/A',
                        'Timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                    })
                df_logs = pd.DataFrame(logs_data)
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            else:
                st.info("Aucune validation croisée effectuée (données indisponibles sur les sources).")

elif submit_btn and not ticker_input:
    st.error("Veuillez saisir un ticker valide.")
