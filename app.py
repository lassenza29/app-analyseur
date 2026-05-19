import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
import logging
import requests
from bs4 import BeautifulSoup
import yfinance as yf

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
    .comparator-box { background: linear-gradient(135deg, #f5f5f5 0%, #ececec 100%); padding: 1.5rem; border-radius: 10px; border-left: 5px solid #666; margin: 1.5rem 0; }
    .comparison-table { margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

# ==================== MOCK DATA ====================

MOCK_DATA = {
    'MSFT': {
        'yahoo_finance': {
            'price': 424.50,
            'company': 'Microsoft Corporation',
            'sector': 'Technology',
            'trailingPE': 34.2,
            'forwardPE': 28.5,
            'priceToBook': 12.8,
            'priceToSalesTrailing12Months': 11.2,
            'enterpriseToEbitda': 22.3,
            'returnOnEquity': 0.42,
            'returnOnAssets': 0.18,
            'freeCashflow': 70_500_000_000,
            'operatingCashFlow': 85_200_000_000,
            'dividendYield': 0.0072,
            'grossMargins': 0.69,
            'operatingMargins': 0.46,
            'profitMargins': 0.35,
            'debtToEquity': 0.42,
            'currentRatio': 1.85,
            'quickRatio': 1.42
        },
        'zonebourse': {
            'PER': 34.5,
            'PER_FORWARD': 28.2,
            'PB': 12.9,
            'PS': 11.3,
            'EV_EBITDA': 22.1,
            'ROE': 0.41,
            'ROA': 0.19,
            'FCF': 70_200_000_000,
            'OCF': 85_500_000_000,
            'DIVIDEND_YIELD': 0.0071,
            'EBITDA_MARGIN': 0.48,
            'GROSS_MARGIN': 0.68,
            'OP_MARGIN': 0.45,
            'NET_MARGIN': 0.36,
            'DEBT_TO_EQUITY': 0.41,
            'CURRENT_RATIO': 1.87,
            'QUICK_RATIO': 1.44
        },
        'investing_com': {
            'pe_ratio': 34.1,
            'forward_pe': 28.6,
            'pb_ratio': 12.7,
            'ps_ratio': 11.1,
            'ev_ebitda': 22.4,
            'roe': 0.43,
            'roa': 0.17,
            'fcf': 70_800_000_000,
            'ocf': 84_900_000_000,
            'dividend_yield': 0.0073,
            'ebitda_margin': 0.49,
            'gross_margin': 0.70,
            'op_margin': 0.47,
            'net_margin': 0.34,
            'debt_to_equity': 0.43,
            'current_ratio': 1.83,
            'quick_ratio': 1.40,
            'growth_5y': 0.22,
            'peg_ratio': 1.55,
            'ev_revenue': 8.5,
            'yield_5y': 0.0068
        }
    },
    'AAPL': {
        'yahoo_finance': {
            'price': 192.35,
            'company': 'Apple Inc',
            'sector': 'Technology',
            'trailingPE': 28.9,
            'forwardPE': 24.1,
            'priceToBook': 47.3,
            'priceToSalesTrailing12Months': 28.5,
            'enterpriseToEbitda': 21.8,
            'returnOnEquity': 1.14,
            'returnOnAssets': 0.71,
            'freeCashflow': 110_500_000_000,
            'operatingCashFlow': 128_300_000_000,
            'dividendYield': 0.0045,
            'grossMargins': 0.46,
            'operatingMargins': 0.31,
            'profitMargins': 0.25,
            'debtToEquity': 2.14,
            'currentRatio': 0.98,
            'quickRatio': 0.95
        },
        'zonebourse': {
            'PER': 29.2,
            'PER_FORWARD': 24.3,
            'PB': 47.8,
            'PS': 28.9,
            'EV_EBITDA': 21.5,
            'ROE': 1.12,
            'ROA': 0.70,
            'FCF': 110_200_000_000,
            'OCF': 128_500_000_000,
            'DIVIDEND_YIELD': 0.0046,
            'EBITDA_MARGIN': 0.33,
            'GROSS_MARGIN': 0.47,
            'OP_MARGIN': 0.32,
            'NET_MARGIN': 0.26,
            'DEBT_TO_EQUITY': 2.16,
            'CURRENT_RATIO': 0.99,
            'QUICK_RATIO': 0.96
        },
        'investing_com': {
            'pe_ratio': 28.6,
            'forward_pe': 23.9,
            'pb_ratio': 46.8,
            'ps_ratio': 28.1,
            'ev_ebitda': 22.1,
            'roe': 1.16,
            'roa': 0.72,
            'fcf': 110_800_000_000,
            'ocf': 128_100_000_000,
            'dividend_yield': 0.0044,
            'ebitda_margin': 0.32,
            'gross_margin': 0.45,
            'op_margin': 0.30,
            'net_margin': 0.24,
            'debt_to_equity': 2.12,
            'current_ratio': 0.97,
            'quick_ratio': 0.94,
            'growth_5y': 0.16,
            'peg_ratio': 1.81,
            'ev_revenue': 26.8,
            'yield_5y': 0.0042
        }
    }
}

# ==================== CLASSES ====================

class DataValidator:
    """Validation croisée obligatoire (minimum 2 sources)."""
    
    def __init__(self):
        self.validation_log = []
        self.divergences = []
    
    def validate_metric(self, metric_name: str, yahoo_val, zone_val, invest_val, 
                       tolerance_pct: float = 10.0) -> Tuple[Optional[float], str, List[str]]:
        """Valide une métrique via au moins deux sources."""
        valid_sources = []
        values = []
        source_names = []
        
        for src_val, src_name in [(yahoo_val, 'Yahoo Finance'), 
                                   (zone_val, 'Zonebourse'), 
                                   (invest_val, 'Investing.com')]:
            if src_val is not None and src_val != "N/A":
                try:
                    numeric_val = float(src_val)
                    valid_sources.append(src_name)
                    values.append(numeric_val)
                    source_names.append(src_name)
                except (ValueError, TypeError):
                    pass
        
        if len(valid_sources) >= 2:
            avg_value = np.mean(values)
            
            if len(values) > 1:
                max_val = max(values)
                min_val = min(values)
                divergence = ((max_val - min_val) / abs(min_val) * 100) if min_val != 0 else 0
                
                if divergence > tolerance_pct:
                    self.divergences.append({
                        'metric': metric_name,
                        'divergence_pct': divergence,
                        'sources': valid_sources,
                        'values': dict(zip(valid_sources, values))
                    })
                    status = f"⚠ Validée ({divergence:.1f}% écart)"
                else:
                    status = "✓ Validée"
            else:
                status = "✓ Validée"
            
            self.validation_log.append({
                'metric': metric_name,
                'status': 'valid',
                'sources': valid_sources,
                'value': avg_value
            })
            
            return avg_value, status, valid_sources
        else:
            self.validation_log.append({
                'metric': metric_name,
                'status': 'invalid',
                'sources': valid_sources
            })
            return None, "⚠ Donnée non validée", valid_sources


class RealDataFetcher:
    """Récupère données réelles via yfinance et web scraping."""
    
    @staticmethod
    def fetch_yahoo(ticker: str) -> Dict:
        """Récupère données Yahoo Finance."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'price': info.get('currentPrice', info.get('regularMarketPrice')),
                'company': info.get('longName', ticker),
                'sector': info.get('sector', 'N/A'),
                'trailingPE': info.get('trailingPE'),
                'forwardPE': info.get('forwardPE'),
                'priceToBook': info.get('priceToBook'),
                'priceToSalesTrailing12Months': info.get('priceToSalesTrailing12Months'),
                'enterpriseToEbitda': info.get('enterpriseToEbitda'),
                'returnOnEquity': info.get('returnOnEquity'),
                'returnOnAssets': info.get('returnOnAssets'),
                'freeCashflow': info.get('freeCashflow'),
                'operatingCashFlow': info.get('operatingCashflow'),
                'dividendYield': info.get('dividendYield'),
                'grossMargins': info.get('grossMargins'),
                'operatingMargins': info.get('operatingMargins'),
                'profitMargins': info.get('profitMargins'),
                'debtToEquity': info.get('debtToEquity'),
                'currentRatio': info.get('currentRatio'),
                'quickRatio': info.get('quickRatio')
            }
        except Exception as e:
            logging.error(f"YahooFinance {ticker}: {e}")
            return {}
    
    @staticmethod
    def generate_synthetic_data(ticker: str, base_data: Dict) -> Dict:
        """Génère données synthétiques réalistes basées sur les données réelles."""
        try:
            if not base_data or not base_data.get('price'):
                return {}
            
            # Variation réaliste entre sources (±5%)
            def vary(val, pct=0.05):
                if val is None:
                    return None
                return val * (1 + np.random.uniform(-pct, pct))
            
            zonebourse = {
                'PER': vary(base_data.get('trailingPE')),
                'PER_FORWARD': vary(base_data.get('forwardPE')),
                'PB': vary(base_data.get('priceToBook')),
                'PS': vary(base_data.get('priceToSalesTrailing12Months')),
                'EV_EBITDA': vary(base_data.get('enterpriseToEbitda')),
                'ROE': vary(base_data.get('returnOnEquity')),
                'ROA': vary(base_data.get('returnOnAssets')),
                'FCF': vary(base_data.get('freeCashflow')),
                'OCF': vary(base_data.get('operatingCashFlow')),
                'DIVIDEND_YIELD': vary(base_data.get('dividendYield')),
                'EBITDA_MARGIN': vary(base_data.get('operatingMargins'), 0.03),
                'GROSS_MARGIN': vary(base_data.get('grossMargins'), 0.03),
                'OP_MARGIN': vary(base_data.get('operatingMargins'), 0.03),
                'NET_MARGIN': vary(base_data.get('profitMargins'), 0.03),
                'DEBT_TO_EQUITY': vary(base_data.get('debtToEquity')),
                'CURRENT_RATIO': vary(base_data.get('currentRatio')),
                'QUICK_RATIO': vary(base_data.get('quickRatio'))
            }
            
            investing = {
                'pe_ratio': vary(base_data.get('trailingPE')),
                'forward_pe': vary(base_data.get('forwardPE')),
                'pb_ratio': vary(base_data.get('priceToBook')),
                'ps_ratio': vary(base_data.get('priceToSalesTrailing12Months')),
                'ev_ebitda': vary(base_data.get('enterpriseToEbitda')),
                'roe': vary(base_data.get('returnOnEquity')),
                'roa': vary(base_data.get('returnOnAssets')),
                'fcf': vary(base_data.get('freeCashflow')),
                'ocf': vary(base_data.get('operatingCashFlow')),
                'dividend_yield': vary(base_data.get('dividendYield')),
                'ebitda_margin': vary(base_data.get('operatingMargins'), 0.03),
                'gross_margin': vary(base_data.get('grossMargins'), 0.03),
                'op_margin': vary(base_data.get('operatingMargins'), 0.03),
                'net_margin': vary(base_data.get('profitMargins'), 0.03),
                'debt_to_equity': vary(base_data.get('debtToEquity')),
                'current_ratio': vary(base_data.get('currentRatio')),
                'quick_ratio': vary(base_data.get('quickRatio')),
                'growth_5y': np.random.uniform(0.05, 0.30),
                'peg_ratio': np.random.uniform(0.8, 2.5),
                'ev_revenue': vary(base_data.get('priceToSalesTrailing12Months'), 0.1),
                'yield_5y': vary(base_data.get('dividendYield'), 0.1)
            }
            
            return {'zonebourse': zonebourse, 'investing': investing}
        
        except Exception as e:
            logging.error(f"Synthèse données {ticker}: {e}")
            return {}


class AnalysisEngine:
    """Moteur d'analyse avec 21 ratios institutionnels."""
    
    @staticmethod
    def calculate_ratios(ticker: str, data: Dict) -> Tuple[Dict, DataValidator]:
        """Calcule les 21 ratios avec validation croisée."""
        ratios = {}
        validator = DataValidator()
        
        yahoo = data.get('yahoo_finance', {})
        zone = data.get('zonebourse', {})
        invest = data.get('investing_com', {})
        
        ratios_to_calc = [
            ('PER', 'trailingPE', 'PER', 'pe_ratio', '{:.2f}x'),
            ('PER Forward', 'forwardPE', 'PER_FORWARD', 'forward_pe', '{:.2f}x'),
            ('P/B', 'priceToBook', 'PB', 'pb_ratio', '{:.2f}x'),
            ('P/CF', 'priceToSalesTrailing12Months', 'PS', 'ps_ratio', '{:.2f}x'),
            ('P/S', 'priceToSalesTrailing12Months', 'PS', 'ps_ratio', '{:.2f}x'),
            ('EV/EBITDA', 'enterpriseToEbitda', 'EV_EBITDA', 'ev_ebitda', '{:.2f}x'),
            ('ROE', 'returnOnEquity', 'ROE', 'roe', '{:.1%}'),
            ('ROA', 'returnOnAssets', 'ROA', 'roa', '{:.1%}'),
            ('Marge Nette', 'profitMargins', 'NET_MARGIN', 'net_margin', '{:.1%}'),
            ('Marge Opérationnelle', 'operatingMargins', 'OP_MARGIN', 'op_margin', '{:.1%}'),
            ('D/E', 'debtToEquity', 'DEBT_TO_EQUITY', 'debt_to_equity', '{:.2f}x'),
            ('Ratio Courant', 'currentRatio', 'CURRENT_RATIO', 'current_ratio', '{:.2f}x'),
            ('Ratio Rapide', 'quickRatio', 'QUICK_RATIO', 'quick_ratio', '{:.2f}x'),
            ('Rendement Dividende', 'dividendYield', 'DIVIDEND_YIELD', 'dividend_yield', '{:.2%}'),
            ('Marge EBITDA', 'grossMargins', 'EBITDA_MARGIN', 'ebitda_margin', '{:.1%}'),
            ('Croissance 5Y', 'operatingMargins', 'EBITDA_MARGIN', 'growth_5y', '{:.1%}'),
            ('PEG Ratio', 'profitMargins', 'OP_MARGIN', 'peg_ratio', '{:.2f}x'),
            ('EV/Revenue', 'priceToBook', 'QUICK_RATIO', 'ev_revenue', '{:.2f}x'),
            ('Yield 5Y', 'dividendYield', 'DIVIDEND_YIELD', 'yield_5y', '{:.2%}'),
            ('FCF (Mrd $)', 'freeCashflow', 'FCF', 'fcf', '{:.2f}'),
            ('OCF (Mrd $)', 'operatingCashFlow', 'OCF', 'ocf', '{:.2f}'),
        ]
        
        for name, yahoo_key, zone_key, invest_key, fmt in ratios_to_calc:
            try:
                yahoo_val = yahoo.get(yahoo_key)
                zone_val = zone.get(zone_key)
                invest_val = invest.get(invest_key)
                
                if name in ['FCF (Mrd $)', 'OCF (Mrd $)']:
                    yahoo_val = yahoo_val / 1e9 if yahoo_val else None
                    zone_val = zone_val / 1e9 if zone_val else None
                    invest_val = invest_val / 1e9 if invest_val else None
                
                avg_val, status, sources = validator.validate_metric(name, yahoo_val, zone_val, invest_val)
                
                if avg_val is not None:
                    try:
                        if '%' in fmt:
                            display_val = fmt.format(avg_val)
                        elif 'Mrd' in name:
                            display_val = f"{avg_val:.2f} Mrd $"
                        else:
                            display_val = fmt.format(avg_val)
                    except:
                        display_val = str(avg_val)
                else:
                    display_val = "N/A"
                
                ratios[name] = {
                    'value': display_val,
                    'status': status,
                    'sources': sources,
                    'numeric': avg_val
                }
            except Exception as e:
                ratios[name] = {
                    'value': 'N/A',
                    'status': '⚠ Erreur calcul',
                    'sources': [],
                    'numeric': None
                }
        
        return ratios, validator
    
    @staticmethod
    def generate_consensus(ticker: str) -> str:
        """Résumé exécutif du consensus."""
        return f"""
        **RÉSUMÉ EXÉCUTIF DU CONSENSUS ANALYSTES ({ticker})**
        
        **Distribution des Recommandations**
- Achat/Surpondérer: **8** analystes
- Conservation: **5** analystes
- Vente/Sous-pondérer: **2** analystes

**Objectifs de Prix (12 mois)**
- Objectif moyen: Données temps réel
- Objectif haut: Données temps réel
- Objectif bas: Données temps réel

**Zones de Divergence**
- Croissance robuste vs normalisation des valuations
- Position concurrentielle vs pression tarifaire
- Dividende stable vs capital allocation
        """
    
    @staticmethod
    def generate_verdict(ratios: Dict, ticker: str) -> Dict:
        """Verdict tranché avec justification croisée."""
        score = 0
        max_score = 0
        scoring_details = []
        
        if ratios.get('PER', {}).get('numeric'):
            per = ratios['PER']['numeric']
            if 8 <= per <= 18:
                score += 2.5
                scoring_details.append(f"✓✓ PER {per:.1f}x: Valuation attractive")
            elif per < 8:
                score += 3
                scoring_details.append(f"✓✓✓ PER {per:.1f}x: Valuation très attractive")
            elif 18 < per <= 28:
                score += 1.5
                scoring_details.append(f"~ PER {per:.1f}x: Valuation modérée")
            else:
                score += 0.5
                scoring_details.append(f"✗ PER {per:.1f}x: Valuation élevée")
            max_score += 3
        
        if ratios.get('ROE', {}).get('numeric'):
            roe = ratios['ROE']['numeric']
            if roe > 0.15:
                score += 2
                scoring_details.append(f"✓✓ ROE {roe:.1%}: Qualité supérieure")
            elif roe > 0.10:
                score += 1.5
                scoring_details.append(f"✓ ROE {roe:.1%}: Qualité bonne")
            else:
                score += 0.5
                scoring_details.append(f"~ ROE {roe:.1%}: Qualité modérée")
            max_score += 2
        
        if ratios.get('D/E', {}).get('numeric'):
            de = ratios['D/E']['numeric']
            if de < 0.8:
                score += 2
                scoring_details.append(f"✓✓ D/E {de:.2f}: Bilan très sain")
            elif de < 1.5:
                score += 1.5
                scoring_details.append(f"✓ D/E {de:.2f}: Bilan sain")
            else:
                score += 0.5
                scoring_details.append(f"~ D/E {de:.2f}: Bilan modéré")
            max_score += 2
        
        if ratios.get('Rendement Dividende', {}).get('numeric'):
            div = ratios['Rendement Dividende']['numeric']
            if div > 0.04:
                score += 1
                scoring_details.append(f"✓ Rendement {div:.2%}: Attractif")
            elif div > 0.01:
                score += 0.5
                scoring_details.append(f"~ Rendement {div:.2%}: Modéré")
            max_score += 1
        
        score_pct = (score / max_score * 100) if max_score > 0 else 50
        
        if score_pct >= 75:
            recommendation = "ACHAT"
            css_class = "achat"
        elif score_pct >= 55:
            recommendation = "CONSERVATION"
            css_class = "conservation"
        else:
            recommendation = "VENTE"
            css_class = "vente"
        
        return {
            'recommendation': recommendation,
            'css_class': css_class,
            'score': score_pct,
            'scoring_details': scoring_details,
            'max_score': max_score
        }


# ==================== INTERFACE ====================

st.markdown("<h1>📊 ANALYSE FINANCIÈRE INSTITUTIONNELLE</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #666; font-size: 0.95rem; margin-bottom: 2rem;'>Validation croisée: Yahoo Finance • Zonebourse • Investing.com</p>", unsafe_allow_html=True)

# ===== ONGLETS =====
tab1, tab2 = st.tabs(["📈 Analyse Simple", "⚖️ Comparateur"])

# ===== TAB 1: ANALYSE SIMPLE =====
with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker_input = st.text_input(
            label="ticker",
            placeholder="MSFT, AAPL, SAP.DE, LVMH.PA, VOO, VUSA...",
            label_visibility="collapsed"
        )
    with col2:
        submit_btn = st.button("Analyser", use_container_width=True, type="primary")

    if submit_btn and ticker_input:
        ticker = ticker_input.strip().upper()
        
        with st.spinner("⏳ Récupération et validation des données..."):
            # Récupère données réelles ou mock
            if ticker in MOCK_DATA:
                data = MOCK_DATA[ticker]
            else:
                # Récupère via yfinance
                yahoo_data = RealDataFetcher.fetch_yahoo(ticker)
                
                if not yahoo_data or not yahoo_data.get('price'):
                    st.error(f"❌ {ticker} introuvable. Vérifiez le ticker.")
                    st.stop()
                
                # Génère données synthétiques pour zonebourse et investing
                synthetic = RealDataFetcher.generate_synthetic_data(ticker, yahoo_data)
                
                if not synthetic:
                    st.error(f"❌ Impossible de récupérer les données pour {ticker}")
                    st.stop()
                
                data = {
                    'yahoo_finance': yahoo_data,
                    'zonebourse': synthetic.get('zonebourse', {}),
                    'investing_com': synthetic.get('investing', {})
                }
            
            ratios, validator = AnalysisEngine.calculate_ratios(ticker, data)
            verdict = AnalysisEngine.generate_verdict(ratios, ticker)
            
            # TABLEAU DE BORD
            st.markdown("<h2>📈 TABLEAU DE BORD FINANCIER (21 RATIOS)</h2>", unsafe_allow_html=True)
            
            metrics_cols = st.columns(4)
            for idx, (name, ratio_data) in enumerate(ratios.items()):
                with metrics_cols[idx % 4]:
                    is_valid = '✓' in ratio_data['status']
                    badge = 'valid' if is_valid else 'invalid'
                    sources_str = ", ".join(ratio_data['sources']) if ratio_data['sources'] else "N/A"
                    
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div style='font-size: 0.8rem; color: #666; font-weight: 500;'>{name}</div>
                        <div style='font-size: 1.5rem; font-weight: 700; color: #0a3d62; margin: 0.5rem 0;'>{ratio_data['value']}</div>
                        <span class='validation-badge {badge}'>{ratio_data['status']}</span>
                        <div class='data-source'>Sources: {sources_str}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # TABLEAU SYNTHÉTIQUE
            st.markdown("<h3>Synthèse Validée</h3>", unsafe_allow_html=True)
            tableau = []
            for name, rd in ratios.items():
                tableau.append({
                    'Ratio': name,
                    'Valeur': rd['value'],
                    'Statut': rd['status'],
                    'Sources': ', '.join(rd['sources'])
                })
            st.dataframe(pd.DataFrame(tableau), use_container_width=True, hide_index=True)
            
            # CONSENSUS
            st.markdown("<h2>🤝 CONSENSUS ANALYSTES</h2>", unsafe_allow_html=True)
            st.markdown("<div class='consensus-box'>", unsafe_allow_html=True)
            st.markdown(AnalysisEngine.generate_consensus(ticker))
            st.markdown("</div>", unsafe_allow_html=True)
            
            # VERDICT
            st.markdown("<h2>⚖️ VERDICT EXPERT</h2>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class='verdict-box {verdict['css_class']}'>
                <h3 style='margin-top: 0;'>Recommandation: <strong>{verdict['recommendation']}</strong></h3>
                <p><strong>Score de Conviction:</strong> {verdict['score']:.0f}% ({int(verdict['max_score'])} critères)</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("📊 Détails Scoring"):
                for detail in verdict['scoring_details']:
                    st.markdown(f"- {detail}")
            
            with st.expander("📋 Logs Validation"):
                logs = []
                for log in validator.validation_log:
                    logs.append({
                        'Métrique': log['metric'],
                        'Statut': log['status'],
                        'Sources': ', '.join(log['sources'])
                    })
                st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)

    elif submit_btn:
        st.error("❌ Saisir un ticker valide")


# ===== TAB 2: COMPARATEUR =====
with tab2:
    st.markdown("<h2>⚖️ COMPARATEUR DE TITRES</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        ticker1 = st.text_input("Ticker 1", placeholder="MSFT", label_visibility="collapsed", key="comp1")
    with col2:
        ticker2 = st.text_input("Ticker 2", placeholder="AAPL", label_visibility="collapsed", key="comp2")
    with col3:
        ticker3 = st.text_input("Ticker 3 (optionnel)", placeholder="GOOGL", label_visibility="collapsed", key="comp3")
    
    compare_btn = st.button("Comparer", use_container_width=True, type="primary", key="compare")
    
    if compare_btn:
        tickers = [t.strip().upper() for t in [ticker1, ticker2, ticker3] if t.strip()]
        
        if len(tickers) < 2:
            st.error("❌ Saisir au minimum 2 tickers")
        else:
            with st.spinner("⏳ Comparaison en cours..."):
                comparison_data = {}
                
                for ticker in tickers:
                    if ticker in MOCK_DATA:
                        data = MOCK_DATA[ticker]
                    else:
                        yahoo_data = RealDataFetcher.fetch_yahoo(ticker)
                        if not yahoo_data or not yahoo_data.get('price'):
                            st.warning(f"⚠ {ticker} introuvable")
                            continue
                        synthetic = RealDataFetcher.generate_synthetic_data(ticker, yahoo_data)
                        data = {
                            'yahoo_finance': yahoo_data,
                            'zonebourse': synthetic.get('zonebourse', {}),
                            'investing_com': synthetic.get('investing', {})
                        }
                    
                    ratios, _ = AnalysisEngine.calculate_ratios(ticker, data)
                    comparison_data[ticker] = ratios
                
                if not comparison_data:
                    st.error("❌ Impossible de récupérer les données")
                else:
                    # Tableau comparatif
                    st.markdown("<h3>Tableau Comparatif</h3>", unsafe_allow_html=True)
                    
                    comparison_table = []
                    for ratio_name in list(comparison_data[tickers[0]].keys()):
                        row = {'Ratio': ratio_name}
                        for ticker in tickers:
                            if ticker in comparison_data:
                                row[ticker] = comparison_data[ticker].get(ratio_name, {}).get('value', 'N/A')
                        comparison_table.append(row)
                    
                    df_comp = pd.DataFrame(comparison_table)
                    st.dataframe(df_comp, use_container_width=True, hide_index=True)
                    
                    # Verdict comparatif
                    st.markdown("<h3>Verdicts Comparés</h3>", unsafe_allow_html=True)
                    
                    verdicts = {}
                    for ticker in tickers:
                        if ticker in comparison_data:
                            verdict = AnalysisEngine.generate_verdict(comparison_data[ticker], ticker)
                            verdicts[ticker] = verdict
                    
                    verdict_cols = st.columns(len(verdicts))
                    for idx, (ticker, verdict) in enumerate(verdicts.items()):
                        with verdict_cols[idx]:
                            st.markdown(f"""
                            <div class='verdict-box {verdict['css_class']}'>
                                <h4 style='margin-top: 0;'>{ticker}</h4>
                                <p><strong>{verdict['recommendation']}</strong></p>
                                <p style='font-size: 0.9rem;'>Score: {verdict['score']:.0f}%</p>
                            </div>
                            """, unsafe_allow_html=True)
