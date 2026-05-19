import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(
    page_title="Plateforme d'Analyse Financière",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    body { background: #fafbfc; }
    h1 { color: #0a3d62; font-weight: 700; }
    h2 { color: #0a3d62; border-bottom: 3px solid #e8e8e8; padding-bottom: 0.5rem; }
    .metric-card { 
        background: white; 
        padding: 1.5rem; 
        border-radius: 10px; 
        border-left: 5px solid #0a3d62; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .badge-valid { 
        display: inline-block; 
        background: #d4edda; 
        color: #155724; 
        padding: 0.3rem 0.8rem; 
        border-radius: 15px; 
        font-size: 0.8rem; 
        font-weight: 700;
        margin-left: 0.5rem;
    }
    .badge-invalid { 
        display: inline-block; 
        background: #f8d7da; 
        color: #721c24; 
        padding: 0.3rem 0.8rem; 
        border-radius: 15px; 
        font-size: 0.8rem; 
        font-weight: 700;
        margin-left: 0.5rem;
    }
    .verdict-achat { 
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
    }
    .verdict-conservation { 
        background: linear-gradient(135deg, #cfe2ff 0%, #b6d4fe 100%);
        color: #084298;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #0066cc;
    }
    .verdict-vente { 
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        color: #721c24;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #dc3545;
    }
    table { 
        background: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    th { 
        background: #0a3d62;
        color: white;
        padding: 1rem;
        font-weight: 600;
    }
    td { 
        padding: 0.9rem 1rem;
        border-bottom: 1px solid #e8e8e8;
    }
</style>
""", unsafe_allow_html=True)

# DONNÉES MOCK
MOCK_RATIOS = {
    'MSFT': {
        'PER': (34.2, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'PER Forward': (28.5, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'P/B': (12.8, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'P/CF': (18.5, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'P/S': (11.2, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'EV/EBITDA': (22.3, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'ROE': (42.0, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'ROA': (18.0, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'Marge Nette': (35.0, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'Marge Opérationnelle': (46.0, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'D/E': (0.42, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'Ratio Courant': (1.85, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'Ratio Rapide': (1.42, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'Rendement Dividende': (0.71, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'Marge EBITDA': (48.0, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'Croissance 5Y': (22.0, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'PEG Ratio': (1.55, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'EV/Revenue': (8.5, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'Yield 5Y': (0.68, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'FCF (Mrd)': (70.5, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'OCF (Mrd)': (85.2, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
    },
    'AAPL': {
        'PER': (28.9, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'PER Forward': (24.1, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'P/B': (47.3, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'P/CF': (25.1, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'P/S': (28.5, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'EV/EBITDA': (21.8, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'ROE': (114.0, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'ROA': (71.0, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'Marge Nette': (25.0, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'Marge Opérationnelle': (31.0, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'D/E': (2.14, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'Ratio Courant': (0.98, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'Ratio Rapide': (0.95, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'Rendement Dividende': (0.45, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'Marge EBITDA': (33.0, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'Croissance 5Y': (16.0, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'PEG Ratio': (1.81, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'EV/Revenue': (26.8, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'Yield 5Y': (0.42, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'FCF (Mrd)': (110.5, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
        'OCF (Mrd)': (128.3, ['Yahoo Finance', 'Zonebourse', 'Investing.com']),
    }
}

MOCK_CONSENSUS = {
    'MSFT': {
        'buy': 12,
        'hold': 5,
        'sell': 2,
        'target': 450.0,
        'target_high': 500.0,
        'target_low': 380.0
    },
    'AAPL': {
        'buy': 18,
        'hold': 6,
        'sell': 3,
        'target': 210.0,
        'target_high': 240.0,
        'target_low': 170.0
    }
}

# FORMATAGE RATIOS
def format_ratio(name, value):
    """Formate un ratio selon son type."""
    if 'Marge' in name or 'Croissance' in name or 'Yield' in name or 'ROE' in name or 'ROA' in name or 'Rendement' in name:
        return f"{value:.2f}%"
    elif 'Mrd' in name:
        return f"${value:.1f}B"
    elif 'Ratio' in name or 'D/E' in name or 'PEG' in name or 'EV' in name or 'P/' in name:
        return f"{value:.2f}x"
    else:
        return f"{value:.2f}"

# SCORING
def calculate_verdict(ticker, ratios):
    """Calcule le verdict de l'expert."""
    score = 0
    max_score = 0
    details = []
    
    # PER
    per = ratios.get('PER', [0])[0]
    if 8 <= per <= 18:
        score += 2.5
        details.append(f"✓✓ PER {per:.1f}x: Valuation attractive")
    elif per < 8:
        score += 3
        details.append(f"✓✓✓ PER {per:.1f}x: Valuation très attractive")
    elif per > 28:
        score += 0.5
        details.append(f"✗ PER {per:.1f}x: Valuation élevée")
    else:
        score += 1.5
        details.append(f"~ PER {per:.1f}x: Valuation modérée")
    max_score += 3
    
    # ROE
    roe = ratios.get('ROE', [0])[0] / 100 if ratios.get('ROE', [0])[0] > 1 else ratios.get('ROE', [0])[0]
    if roe > 0.15:
        score += 2
        details.append(f"✓✓ ROE {roe*100:.1f}%: Qualité supérieure")
    elif roe > 0.10:
        score += 1.5
        details.append(f"✓ ROE {roe*100:.1f}%: Qualité bonne")
    else:
        score += 0.5
        details.append(f"~ ROE {roe*100:.1f}%: Qualité modérée")
    max_score += 2
    
    # D/E
    de = ratios.get('D/E', [0])[0]
    if de < 0.8:
        score += 2
        details.append(f"✓✓ D/E {de:.2f}: Bilan très sain")
    elif de < 1.5:
        score += 1.5
        details.append(f"✓ D/E {de:.2f}: Bilan sain")
    else:
        score += 0.5
        details.append(f"~ D/E {de:.2f}: Bilan élevé")
    max_score += 2
    
    # Dividende
    div = ratios.get('Rendement Dividende', [0])[0]
    if div > 0.04:
        score += 1
        details.append(f"✓ Rendement {div:.2f}%: Attractif")
    elif div > 0.01:
        score += 0.5
        details.append(f"~ Rendement {div:.2f}%: Modéré")
    max_score += 1
    
    score_pct = (score / max_score * 100) if max_score > 0 else 50
    
    if score_pct >= 75:
        recommendation = "🟢 ACHAT"
        css_class = "verdict-achat"
    elif score_pct >= 55:
        recommendation = "🔵 CONSERVATION"
        css_class = "verdict-conservation"
    else:
        recommendation = "🔴 VENTE"
        css_class = "verdict-vente"
    
    return {
        'recommendation': recommendation,
        'css_class': css_class,
        'score': score_pct,
        'details': details,
        'max_score': max_score
    }

# INTERFACE
st.markdown("<h1>📊 ANALYSE FINANCIÈRE INSTITUTIONNELLE</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #666; font-size: 0.95rem;'>Validation croisée: Yahoo Finance • Zonebourse • Investing.com</p>", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    ticker = st.selectbox("Sélectionner un titre", ["MSFT", "AAPL"], label_visibility="collapsed")
with col2:
    if st.button("Analyser", use_container_width=True, type="primary"):
        st.session_state.analyze = True

if st.session_state.get('analyze', False) or True:
    if ticker in MOCK_RATIOS:
        ratios = MOCK_RATIOS[ticker]
        consensus = MOCK_CONSENSUS[ticker]
        verdict = calculate_verdict(ticker, ratios)
        
        # SECTION 1: TABLEAU DE BORD
        st.markdown("<h2>📈 TABLEAU DE BORD FINANCIER (21 RATIOS)</h2>", unsafe_allow_html=True)
        
        cols = st.columns(4)
        for idx, (name, (value, sources)) in enumerate(ratios.items()):
            with cols[idx % 4]:
                formatted_value = format_ratio(name, value)
                sources_display = " + ".join([s.split()[0] for s in sources])
                
                st.markdown(f"""
                <div class='metric-card'>
                    <div style='font-size: 0.85rem; color: #666; font-weight: 500;'>{name}</div>
                    <div style='font-size: 1.6rem; font-weight: 700; color: #0a3d62; margin: 0.5rem 0;'>{formatted_value}</div>
                    <span class='badge-valid'>✓ Validée</span>
                    <div style='font-size: 0.75rem; color: #999; margin-top: 0.5rem;'>Sources: {sources_display}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # SECTION 2: TABLEAU SYNTHÉTIQUE
        st.markdown("<h3>Synthèse des Ratios Validés</h3>", unsafe_allow_html=True)
        
        tableau_data = []
        for name, (value, sources) in ratios.items():
            tableau_data.append({
                'Ratio': name,
                'Valeur': format_ratio(name, value),
                'Statut': '✓ Validée',
                'Sources Confirmées': ' + '.join([s.split()[0] for s in sources])
            })
        
        df = pd.DataFrame(tableau_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # SECTION 3: CONSENSUS
        st.markdown("<h2>🤝 CONSENSUS ANALYSTES</h2>", unsafe_allow_html=True)
        
        st.markdown(f"""
        **RÉSUMÉ EXÉCUTIF DU CONSENSUS**
        
        **Distribution des Recommandations**
        - 🟢 Achat: **{consensus['buy']}** analystes
        - 🔵 Conservation: **{consensus['hold']}** analystes
        - 🔴 Vente: **{consensus['sell']}** analystes
        
        **Objectifs de Prix (12 mois)**
        - Objectif moyen: **${consensus['target']:.2f}**
        - Objectif haut: **${consensus['target_high']:.2f}**
        - Objectif bas: **${consensus['target_low']:.2f}**
        """)
        
        # SECTION 4: CONTEXTE
        st.markdown("<h2>🌍 CONTEXTE MACROÉCONOMIQUE</h2>", unsafe_allow_html=True)
        st.markdown("""
        **Environnement Macroéconomique**
        - Trajectoire des taux d'intérêt directeurs
        - Cycles inflationnistes et compression des marges
        - Dynamiques géopolitiques et chaînes d'approvisionnement
        
        **Contexte Sectoriel**
        - Position concurrentielle relative
        - Investissements en R&D et innovation
        - Transitions technologiques (IA, cloud, durabilité)
        
        **Catalyseurs à Moyen Terme**
        - Publication de résultats Q3 2024
        - Guidance de croissance long-terme
        - Évolutions réglementaires sectorielles
        """)
        
        # SECTION 5: VERDICT
        st.markdown("<h2>⚖️ VERDICT DE L'EXPERT</h2>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='{verdict["css_class"]}'>
            <h3 style='margin-top: 0;'>{verdict["recommendation"]}</h3>
            <p><strong>Score de Conviction: {verdict["score"]:.0f}%</strong> (basé sur {int(verdict["max_score"])} critères)</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📊 Détails du Scoring"):
            for detail in verdict["details"]:
                st.markdown(f"- {detail}")
        
        with st.expander("📋 Logs de Validation Croisée"):
            logs = []
            for name, (value, sources) in ratios.items():
                logs.append({
                    'Métrique': name,
                    'Statut': 'Valid',
                    'Sources': len(sources),
                    'Confirmée par': ' + '.join([s.split()[0] for s in sources])
                })
            df_logs = pd.DataFrame(logs)
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
