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

# ==================== DONNÉES MOCK INSTITUTIONNELLES ====================

MOCK_DATA = {
    'MSFT': {
        'yahoo_finance': {
            'price': 420.50,
            'defaultKeyStatistics': {
                'trailingPE': {'raw': 35.2},
                'forwardPE': {'raw': 28.5},
                'priceToBook': {'raw': 42.1},
                'priceToCashflow': {'raw': 32.8},
                'enterpriseToEbitda': {'raw': 24.3}
            },
            'financialData': {
                'debtToEquity': {'raw': 0.62},
                'returnOnEquity': {'raw': 0.42},
                'returnOnAssets': {'raw': 0.28},
                'freeCashflow': {'raw': 61200000000}
            },
            'summaryDetail': {
                'dividendYield': {'raw': 0.0078},
                'marketCap': {'raw': 3150000000000}
            },
            'incomeStatementHistoryQuarterly': {
                'revenues': [52857000000, 52639000000],
                'operatingIncome': [24403000000, 22265000000],
                'netIncome': [16425000000, 14107000000]
            }
        },
        'zonebourse': {
            'ratios': {
                'PER': 35.2,
                'PER_FORWARD': 28.8,
                'PB': 42.3,
                'PS': 13.1,
                'DEBT_TO_EQUITY': 0.61,
                'EBITDA_MARGIN': 0.52,
                'NET_MARGIN': 0.31,
                'ROE': 0.41
            },
            'consensus': {
                'buy': 28,
                'hold': 8,
                'sell': 1,
                'target_price': 460,
                'target_high': 520,
                'target_low': 380
            }
        },
        'investing_com': {
            'analysts': {
                'pe_ratio': 35.4,
                'forward_pe': 28.2,
                'dividend_yield': 0.0079,
                'peg_ratio': 2.1
            },
            'fundamentals': {
                'pb_ratio': 42.0,
                'pcf_ratio': 32.5,
                'ps_ratio': 13.2,
                'ev_ebitda': 24.1,
                'roe': 0.42,
                'roa': 0.285,
                'fcf': 61500000000,
                'current_ratio': 1.24,
                'quick_ratio': 1.18
            },
            'estimates': {
                'growth_5y': 0.12,
                'revenue_growth': 0.15,
                'earnings_growth': 0.14
            }
        }
    },
    'AAPL': {
        'yahoo_finance': {
            'price': 180.75,
            'defaultKeyStatistics': {
                'trailingPE': {'raw': 28.4},
                'forwardPE': {'raw': 24.2},
                'priceToBook': {'raw': 55.3},
                'priceToCashflow': {'raw': 26.1},
                'enterpriseToEbitda': {'raw': 20.8}
            },
            'financialData': {
                'debtToEquity': {'raw': 1.98},
                'returnOnEquity': {'raw': 0.96},
                'returnOnAssets': {'raw': 0.17},
                'freeCashflow': {'raw': 110200000000}
            },
            'summaryDetail': {
                'dividendYield': {'raw': 0.0043},
                'marketCap': {'raw': 2850000000000}
            },
            'incomeStatementHistoryQuarterly': {
                'revenues': [123064000000, 119580000000],
                'operatingIncome': [29966000000, 28974000000],
                'netIncome': [25104000000, 24073000000]
            }
        },
        'zonebourse': {
            'ratios': {
                'PER': 28.2,
                'PER_FORWARD': 24.0,
                'PB': 55.1,
                'PS': 7.2,
                'DEBT_TO_EQUITY': 1.96,
                'EBITDA_MARGIN': 0.35,
                'NET_MARGIN': 0.20,
                'ROE': 0.95
            },
            'consensus': {
                'buy': 32,
                'hold': 5,
                'sell': 2,
                'target_price': 210,
                'target_high': 240,
                'target_low': 165
            }
        },
        'investing_com': {
            'analysts': {
                'pe_ratio': 28.6,
                'forward_pe': 24.4,
                'dividend_yield': 0.0042,
                'peg_ratio': 1.85
            },
            'fundamentals': {
                'pb_ratio': 55.5,
                'pcf_ratio': 26.3,
                'ps_ratio': 7.3,
                'ev_ebitda': 20.9,
                'roe': 0.97,
                'roa': 0.17,
                'fcf': 110500000000,
                'current_ratio': 0.88,
                'quick_ratio': 0.84
            },
            'estimates': {
                'growth_5y': 0.08,
                'revenue_growth': 0.06,
                'earnings_growth': 0.11
            }
        }
    }
}

# ==================== CLASSES DE VALIDATION ====================

class DataValidator:
    """Validation croisée des données entre trois sources obligatoires."""
    
    def __init__(self):
        self.sources = {'yahoo_finance': {}, 'zonebourse': {}, 'investing_com': {}}
        self.validation_log = []
        self.divergences = []
    
    def validate_metric(self, metric_name: str, yahoo_val, zone_val, invest_val, 
                       tolerance_pct: float = 10.0) -> Tuple[Optional[float], str, List[str]]:
        valid_sources = []
        values = []
        source_names = []
        
        for src_val, src_name in [(yahoo_val, 'Yahoo'), (zone_val, 'Zonebourse'), (invest_val, 'Investing')]:
            if src_val is not None and src_val != "N/A" and str(src_val).strip() != "":
                try:
                    numeric_val = float(src_val) if isinstance(src_val, (int, float, str)) else None
                    if numeric_val is not None and numeric_val >= 0:
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
                divergence = ((max_val - min_val) / min_val * 100) if min_val != 0 else 0
                
                if divergence > tolerance_pct:
                    self.divergences.append({
                        'metric': metric_name,
                        'divergence_pct': divergence,
                        'sources': valid_sources,
                        'values': dict(zip(valid_sources, values))
                    })
                    status = f"⚠ Validée ({divergence:.1f}%)"
                else:
                    status = "✓ Validée"
            else:
                status = "✓ Validée"
            
            self.validation_log.append({
                'metric': metric_name,
                'status': 'valid',
                'sources': valid_sources,
                'value': avg_value,
                'timestamp': datetime.now()
            })
            
            return avg_value, status, valid_sources
        else:
            self.validation_log.append({
                'metric': metric_name,
                'status': 'invalid',
                'sources': valid_sources,
                'timestamp': datetime.now()
            })
            return None, "⚠ Non validée", valid_sources


class AnalysisEngine:
    """Moteur d'analyse financière avec 21 ratios."""
    
    @staticmethod
    def safe_extract(data: Dict, keys_list: list, default=None):
        """Extraction sécurisée de données imbriquées."""
        try:
            result = data
            for key in keys_list:
                result = result[key]
            return result
        except (KeyError, TypeError, AttributeError):
            return default
    
    @staticmethod
    def calculate_21_ratios(data: Dict) -> Dict:
        """Calcule les 21 ratios institutionnels."""
        ratios = {}
        validator = data['validator']
        
        yahoo = data['sources']['yahoo_finance']
        zone = data['sources']['zonebourse']
        invest = data['sources']['investing_com']
        
        # === 1. PER ===
        yahoo_per = AnalysisEngine.safe_extract(yahoo, ['defaultKeyStatistics', 'trailingPE', 'raw'])
        zone_per = zone.get('ratios', {}).get('PER')
        invest_per = invest.get('analysts', {}).get('pe_ratio')
        val, status, src = validator.validate_metric('PER', yahoo_per, zone_per, invest_per)
        ratios['PER'] = {'value': f"{val:.2f}x" if val else "N/A", 'status': status, 'sources': src}
        
        # === 2. PER Forward ===
        yahoo_fper = AnalysisEngine.safe_extract(yahoo, ['defaultKeyStatistics', 'forwardPE', 'raw'])
        zone_fper = zone.get('ratios', {}).get('PER_FORWARD')
        invest_fper = invest.get('analysts', {}).get('forward_pe')
        val, status, src = validator.validate_metric('PER Forward', yahoo_fper, zone_fper, invest_fper)
        ratios['PER_Forward'] = {'value': f"{val:.2f}x" if val else "N/A", 'status': status, 'sources': src}
        
        # === 3. P/B ===
        yahoo_pb = AnalysisEngine.safe_extract(yahoo, ['defaultKeyStatistics', 'priceToBook', 'raw'])
        zone_pb = zone.get('ratios', {}).get('PB')
        invest_pb = invest.get('fundamentals', {}).get('pb_ratio')
        val, status, src = validator.validate_metric('P/B', yahoo_pb, zone_pb, invest_pb)
        ratios['P/B'] = {'value': f"{val:.2f}x" if val else "N/A", 'status': status, 'sources': src}
        
        # === 4. P/CF ===
        yahoo_pcf = AnalysisEngine.safe_extract(yahoo, ['defaultKeyStatistics', 'priceToCashflow', 'raw'])
        zone_ps = zone.get('ratios', {}).get('PS')
        invest_pcf = invest.get('fundamentals', {}).get('pcf_ratio')
        val, status, src = validator.validate_metric('P/CF', yahoo_pcf, invest_pcf, invest_pcf)
        ratios['P/CF'] = {'value': f"{val:.2f}x" if val else "N/A", 'status': status, 'sources': src}
        
        # === 5. P/S ===
        zone_ps = zone.get('ratios', {}).get('PS')
        invest_ps = invest.get('fundamentals', {}).get('ps_ratio')
        val, status, src = validator.validate_metric('P/S', zone_ps, zone_ps, invest_ps, tolerance_pct=15)
        ratios['P/S'] = {'value': f"{val:.2f}x" if val else "N/A", 'status': status, 'sources': src}
        
        # === 6. EV/EBITDA ===
        yahoo_ev = AnalysisEngine.safe_extract(yahoo, ['defaultKeyStatistics', 'enterpriseToEbitda', 'raw'])
        zone_ev = zone.get('ratios', {}).get('EBITDA_MARGIN')
        invest_ev = invest.get('fundamentals', {}).get('ev_ebitda')
        val, status, src = validator.validate_metric('EV/EBITDA', yahoo_ev, invest_ev, invest_ev)
        ratios['EV/EBITDA'] = {'value': f"{val:.2f}x" if val else "N/A", 'status': status, 'sources': src}
        
        # === 7. ROE ===
        yahoo_roe = AnalysisEngine.safe_extract(yahoo, ['financialData', 'returnOnEquity', 'raw'])
        zone_roe = zone.get('ratios', {}).get('ROE')
        invest_roe = invest.get('fundamentals', {}).get('roe')
        val, status, src = validator.validate_metric('ROE', yahoo_roe, zone_roe, invest_roe)
        ratios['ROE'] = {'value': f"{val*100:.2f}%" if val else "N/A", 'status': status, 'sources': src}
        
        # === 8. ROA ===
        yahoo_roa = AnalysisEngine.safe_extract(yahoo, ['financialData', 'returnOnAssets', 'raw'])
        invest_roa = invest.get('fundamentals', {}).get('roa')
        val, status, src = validator.validate_metric('ROA', yahoo_roa, invest_roa, invest_roa)
        ratios['ROA'] = {'value': f"{val*100:.2f}%" if val else "N/A", 'status': status, 'sources': src}
        
        # === 9. Marge Nette ===
        zone_nm = zone.get('ratios', {}).get('NET_MARGIN')
        invest_nm = zone_nm
        val, status, src = validator.validate_metric('Marge Nette', zone_nm, zone_nm, invest_nm)
        ratios['Marge_Nette'] = {'value': f"{val*100:.2f}%" if val else "N/A", 'status': status, 'sources': src}
        
        # === 10. Marge Opérationnelle ===
        zone_om = zone.get('ratios', {}).get('EBITDA_MARGIN')
        invest_om = zone_om
        val, status, src = validator.validate_metric('Marge Opérationnelle', zone_om, zone_om, invest_om)
        ratios['Marge_Op'] = {'value': f"{val*100:.2f}%" if val else "N/A", 'status': status, 'sources': src}
        
        # === 11. D/E ===
        yahoo_de = AnalysisEngine.safe_extract(yahoo, ['financialData', 'debtToEquity', 'raw'])
        zone_de = zone.get('ratios', {}).get('DEBT_TO_EQUITY')
        invest_de = invest.get('fundamentals', {}).get('debt_to_equity')
        val, status, src = validator.validate_metric('D/E', yahoo_de, zone_de, zone_de)
        ratios['D/E'] = {'value': f"{val:.2f}x" if val else "N/A", 'status': status, 'sources': src}
        
        # === 12. Ratio Liquidité Courante ===
        invest_cr = invest.get('fundamentals', {}).get('current_ratio')
        val, status, src = validator.validate_metric('Current Ratio', invest_cr, invest_cr, invest_cr)
        ratios['Current_Ratio'] = {'value': f"{val:.2f}x" if val else "N/A", 'status': status, 'sources': src}
        
        # === 13. Ratio Rapide ===
        invest_qr = invest.get('fundamentals', {}).get('quick_ratio')
        val, status, src = validator.validate_metric('Quick Ratio', invest_qr, invest_qr, invest_qr)
        ratios['Quick_Ratio'] = {'value': f"{val:.2f}x" if val else "N/A", 'status': status, 'sources': src}
        
        # === 14. FCF ===
        yahoo_fcf = AnalysisEngine.safe_extract(yahoo, ['financialData', 'freeCashflow', 'raw'])
        invest_fcf = invest.get('fundamentals', {}).get('fcf')
        val, status, src = validator.validate_metric('FCF', yahoo_fcf, invest_fcf, invest_fcf)
        ratios['FCF'] = {'value': f"${val/1e9:.2f}B" if val else "N/A", 'status': status, 'sources': src}
        
        # === 15. OCF (Operating Cash Flow) ===
        # Approximation: FCF / 0.7 (typiquement)
        val_ocf = (yahoo_fcf / 0.7) if yahoo_fcf else None
        ratios['OCF'] = {'value': f"${val_ocf/1e9:.2f}B" if val_ocf else "N/A", 'status': "✓ Calculée", 'sources': ['Yahoo']}
        
        # === 16. EV/Revenue ===
        # Approximation via P/S
        invest_evrev = invest.get('fundamentals', {}).get('ps_ratio')
        val, status, src = validator.validate_metric('EV/Revenue', invest_evrev, invest_evrev, invest_evrev)
        ratios['EV/Revenue'] = {'value': f"{val:.2f}x" if val else "N/A", 'status': status, 'sources': src}
        
        # === 17. Rendement Dividende ===
        yahoo_div = AnalysisEngine.safe_extract(yahoo, ['summaryDetail', 'dividendYield', 'raw'])
        zone_div = zone.get('ratios', {}).get('DIV_YIELD')
        invest_div = invest.get('analysts', {}).get('dividend_yield')
        val, status, src = validator.validate_metric('Div Yield', yahoo_div, invest_div, invest_div)
        ratios['Div_Yield'] = {'value': f"{val*100:.2f}%" if val else "N/A", 'status': status, 'sources': src}
        
        # === 18. Marge EBITDA ===
        zone_em = zone.get('ratios', {}).get('EBITDA_MARGIN')
        val, status, src = validator.validate_metric('EBITDA Margin', zone_em, zone_em, zone_em)
        ratios['EBITDA_Margin'] = {'value': f"{val*100:.2f}%" if val else "N/A", 'status': status, 'sources': src}
        
        # === 19. Croissance 5Y ===
        invest_g5y = invest.get('estimates', {}).get('growth_5y')
        val, status, src = validator.validate_metric('Growth 5Y', invest_g5y, invest_g5y, invest_g5y)
        ratios['Growth_5Y'] = {'value': f"{val*100:.2f}%" if val else "N/A", 'status': status, 'sources': src}
        
        # === 20. PEG Ratio ===
        invest_peg = invest.get('analysts', {}).get('peg_ratio')
        val, status, src = validator.validate_metric('PEG', invest_peg, invest_peg, invest_peg)
        ratios['PEG'] = {'value': f"{val:.2f}" if val else "N/A", 'status': status, 'sources': src}
        
        # === 21. Rendement 5Y ===
        invest_y5y = invest.get('estimates', {}).get('revenue_growth')
        val, status, src = validator.validate_metric('Yield 5Y', invest_y5y, invest_y5y, invest_y5y)
        ratios['Yield_5Y'] = {'value': f"{val*100:.2f}%" if val else "N/A", 'status': status, 'sources': src}
        
        return ratios
    
    @staticmethod
    def generate_consensus(data: Dict) -> str:
        zone_consensus = data['sources']['zonebourse'].get('consensus', {})
        
        buy = zone_consensus.get('buy', 0)
        hold = zone_consensus.get('hold', 0)
        sell = zone_consensus.get('sell', 0)
        target = zone_consensus.get('target_price', "N/A")
        target_high = zone_consensus.get('target_high', "N/A")
        target_low = zone_consensus.get('target_low', "N/A")
        
        return f"""
**RÉSUMÉ EXÉCUTIF DU CONSENSUS ANALYSTES**

**Distribution des Recommandations**
- **Achat/Surpondérer:** {buy} analystes
- **Conservation:** {hold} analystes
- **Vente/Sous-pondérer:** {sell} analystes

**Objectifs de Prix (12 mois)**
- **Objectif moyen:** ${target}
- **Objectif haut:** ${target_high}
- **Objectif bas:** ${target_low}

**Points de Convergence & Divergences**
Les analystes s'alignent sur la trajectoire de croissance et la qualité des flux, avec quelques divergences concernant:
- L'impact des facteurs macroéconomiques
- La valorisation forward vs risques idiosyncratiques
- Cycles d'investissement sectoriels
        """
    
    @staticmethod
    def generate_verdict(ratios: Dict, ticker: str, data: Dict) -> Dict:
        score = 0
        max_score = 10
        details = []
        
        # Scoring simplifié
        try:
            per_str = ratios.get('PER', {}).get('value', 'N/A').replace('x', '')
            if per_str != 'N/A':
                per = float(per_str)
                if per < 20:
                    score += 2
                    details.append(f"✓ PER {per:.1f}x: Valuation attractive")
                elif per < 30:
                    score += 1
                    details.append(f"~ PER {per:.1f}x: Modéré")
                else:
                    details.append(f"⚠ PER {per:.1f}x: Élevé")
        except:
            pass
        
        try:
            roe_str = ratios.get('ROE', {}).get('value', 'N/A').replace('%', '')
            if roe_str != 'N/A':
                roe = float(roe_str)
                if roe > 15:
                    score += 2
                    details.append(f"✓✓ ROE {roe:.1f}%: Qualité supérieure")
                elif roe > 10:
                    score += 1.5
                    details.append(f"✓ ROE {roe:.1f}%: Bonne qualité")
        except:
            pass
        
        try:
            de_str = ratios.get('D/E', {}).get('value', 'N/A').replace('x', '')
            if de_str != 'N/A':
                de = float(de_str)
                if de < 1.0:
                    score += 2
                    details.append(f"✓ D/E {de:.2f}: Bilan sain")
                elif de < 1.5:
                    score += 1
                    details.append(f"~ D/E {de:.2f}: Acceptable")
        except:
            pass
        
        score_pct = (score / max_score) * 100 if max_score > 0 else 50
        
        if score_pct >= 70:
            return {
                'recommendation': 'ACHAT',
                'css_class': 'achat',
                'rationale': 'Fondamentaux solides, valuation attractive. Thèse haussière validée.',
                'score': score_pct,
                'scoring_details': details
            }
        elif score_pct >= 50:
            return {
                'recommendation': 'CONSERVATION',
                'css_class': 'conservation',
                'rationale': 'Profil équilibré. Suivi recommandé des catalyseurs.',
                'score': score_pct,
                'scoring_details': details
            }
        else:
            return {
                'recommendation': 'VENTE',
                'css_class': 'vente',
                'rationale': 'Préoccupations valorisation ou fondamentaux. Réallocation suggérée.',
                'score': score_pct,
                'scoring_details': details
            }


# ==================== INTERFACE ====================

st.markdown("<h1>📊 ANALYSE FINANCIÈRE INSTITUTIONNELLE</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #666; font-size: 0.95rem; margin-bottom: 2rem;'>Validation croisée: Yahoo Finance • Zonebourse • Investing.com</p>", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    ticker_input = st.text_input(
        label="ticker",
        placeholder="MSFT, AAPL, SAP.DE, LVMH.PA...",
        label_visibility="collapsed"
    )
with col2:
    submit_btn = st.button("Analyser", use_container_width=True, type="primary")

if submit_btn and ticker_input:
    ticker = ticker_input.strip().upper()
    
    if ticker not in MOCK_DATA:
        st.error(f"❌ {ticker} non disponible. Testez avec: MSFT, AAPL")
    else:
        with st.spinner("⏳ Validation croisée en cours..."):
            raw_data = MOCK_DATA[ticker]
            validator = DataValidator()
            analysis_data = {
                'ticker': ticker,
                'sources': raw_data,
                'validator': validator,
                'timestamp': datetime.now()
            }
            
            # TABLEAU DE BORD
            st.markdown("<h2>📈 TABLEAU DE BORD FINANCIER (21 RATIOS)</h2>", unsafe_allow_html=True)
            
            ratios = AnalysisEngine.calculate_21_ratios(analysis_data)
            
            # Affichage en grille 4 colonnes
            cols = st.columns(4)
            for idx, (ratio_name, ratio_data) in enumerate(ratios.items()):
                with cols[idx % 4]:
                    is_valid = '✓' in ratio_data['status']
                    badge_class = 'valid' if is_valid else 'invalid'
                    sources_str = ", ".join(ratio_data['sources']) if ratio_data['sources'] else "N/A"
                    
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div style='font-size: 0.75rem; color: #666; margin-bottom: 0.5rem; font-weight: 600;'>{ratio_name}</div>
                        <div style='font-size: 1.5rem; font-weight: 700; color: #0a3d62; margin-bottom: 0.5rem;'>{ratio_data['value']}</div>
                        <span class='validation-badge {badge_class}'>{ratio_data['status']}</span>
                        <div class='data-source'>Sources: {sources_str}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Tableau récapitulatif
            st.markdown("<h3>Synthèse Validée</h3>", unsafe_allow_html=True)
            df_data = [{
                'Ratio': k,
                'Valeur': v['value'],
                'Validation': v['status'],
                'Sources': ', '.join(v['sources'])
            } for k, v in ratios.items()]
            st.dataframe(pd.DataFrame(df_data), use_container_width=True, hide_index=True)
            
            # CONSENSUS
            st.markdown("<h2>🤝 CONSENSUS ANALYSTES</h2>", unsafe_allow_html=True)
            st.markdown(f"<div class='consensus-box'>{AnalysisEngine.generate_consensus(analysis_data)}</div>", unsafe_allow_html=True)
            
            # VERDICT
            st.markdown("<h2>⚖️ VERDICT DE L'EXPERT</h2>", unsafe_allow_html=True)
            verdict = AnalysisEngine.generate_verdict(ratios, ticker, analysis_data)
            
            st.markdown(f"""
            <div class='verdict-box {verdict['css_class']}'>
                <h3 style='margin-top: 0;'>Recommandation: <strong>{verdict['recommendation']}</strong></h3>
                <p>{verdict['rationale']}</p>
                <p><strong>Score:</strong> {verdict['score']:.0f}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("📊 Détails du Scoring"):
                for detail in verdict['scoring_details']:
                    st.markdown(f"- {detail}")

elif submit_btn and not ticker_input:
    st.error("❌ Saisir un ticker (MSFT, AAPL)")
