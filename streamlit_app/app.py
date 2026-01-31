"""
TheSentient - Backtesting Dashboard (Streamlit)
Tab Backtesting: Simulazione massiva Earning Report Genius
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from ticker_data import get_sp500_tickers, get_nasdaq100_tickers, get_tickers_with_sectors
from backtest_engine import (
    fetch_historical_earnings,
    run_historical_simulation,
    aggregate_results,
    bot_logic_placeholder,
)

st.set_page_config(page_title="TheSentient Backtesting", page_icon="📊", layout="wide")

st.title("📊 Backtesting - Earning Report Genius")
st.markdown("*Simulazione storica massiva (What-If Analysis)*")

# Sidebar: Configurazione
with st.sidebar:
    st.header("⚙️ Configurazione")

    universe = st.selectbox(
        "Universo ticker",
        ["S&P 500", "Nasdaq 100"],
        index=0,
    )
    tickers_raw = get_sp500_tickers() if universe == "S&P 500" else get_nasdaq100_tickers()
    max_tickers = st.slider("Limite ticker (per test rapidi)", 50, len(tickers_raw), min(200, len(tickers_raw)))
    tickers = tickers_raw[:max_tickers]

    start_year = st.number_input("Anno inizio", 2015, 2024, 2020)
    end_year = st.number_input("Anno fine", 2015, 2025, 2024)
    if start_year > end_year:
        st.error("Anno inizio deve essere ≤ anno fine")
        st.stop()

    sample_days = st.selectbox("Sample giorni (1=completo, 7=veloce)", [1, 3, 7], index=0, format_func=lambda x: f"Ogni {x} giorni" if x > 1 else "Completo (ogni giorno)")
    capital_per_trade = st.number_input("Capitale per trade ($)", 100, 10000, 1000)
    min_confidence = st.slider("Confidence minima bot (%)", 0, 80, 30)
    use_cache = st.checkbox("Usa cache dati", value=True)

    st.divider()
    st.caption("Il sistema usa la logica Earning Report Genius (placeholder) per ogni evento earnings storico.")

# Tab principale
tab1, tab2, tab3 = st.tabs(["▶️ Esegui Backtest", "📈 Report", "ℹ️ Info"])

with tab1:
    st.subheader("Avvia simulazione")
    run_btn = st.button("🚀 Avvia Backtest", type="primary")
    if run_btn:
        progress_bar = st.progress(0, text="Inizializzazione...")
        status = st.empty()
        results_container = st.empty()

        try:
            # Fase 1: Data Ingestion
            status.info("Fase 1/2: Scaricamento earnings storici...")
            earnings = fetch_historical_earnings(
                tickers,
                start_year,
                end_year,
                progress_callback=lambda d, t, msg: progress_bar.progress(min(d / t, 1.0), text=msg) if t > 0 else None,
                use_cache=use_cache,
                sample_days=sample_days,
            )

            if not earnings:
                status.warning("Nessun evento earnings trovato per il periodo. Prova con più ticker o un altro intervallo.")
                progress_bar.empty()
            else:
                status.info(f"Trovati {len(earnings)} eventi earnings. Arricchimento settori...")
                sectors = get_tickers_with_sectors(list(set(e["symbol"] for e in earnings)))
                for e in earnings:
                    e["sector"] = sectors.get(e["symbol"], "Unknown")

                # Fase 2: Simulation Loop
                status.info("Fase 2/2: Esecuzione simulazione...")
                results = run_historical_simulation(
                    earnings,
                    capital_per_trade=capital_per_trade,
                    bot_logic=bot_logic_placeholder,
                    progress_callback=lambda i, t, msg: progress_bar.progress(min((i + 1) / t, 1.0), text=msg) if t > 0 else None,
                    min_confidence=min_confidence,
                )

                progress_bar.progress(1.0, text="Completato!")
                status.success("Backtest completato!")

                # Salva in session state per tab Report
                st.session_state["backtest_results"] = results
                st.session_state["backtest_earnings_count"] = len(earnings)

                # Anteprima risultati
                with results_container.container():
                    st.subheader("Anteprima risultati")
                    df = pd.DataFrame(results)
                    traded = df[df["decision"] == "BUY"]
                    if not traded.empty:
                        agg = aggregate_results(results)
                        st.metric("Trade eseguiti", agg["total_trades"])
                        st.metric("Win Rate", f"{agg['win_rate']}%")
                        st.metric("P&L totale", f"${agg['total_pnl']:,.2f}")
                    st.dataframe(df.tail(50), use_container_width=True)

        except Exception as e:
            status.error(f"Errore: {e}")
            import traceback
            st.code(traceback.format_exc())
        finally:
            progress_bar.empty()

with tab2:
    st.subheader("Report aggregato")
    if "backtest_results" not in st.session_state:
        st.info("Esegui prima un backtest dalla tab 'Esegui Backtest'.")
    else:
        results = st.session_state["backtest_results"]
        df = pd.DataFrame(results)

        # Filtri
        col1, col2, col3 = st.columns(3)
        with col1:
            years = sorted(df["year"].unique()) if "year" in df.columns else []
            filter_year = st.selectbox("Filtra per anno", ["Tutti"] + [str(y) for y in years])
        with col2:
            sectors = ["Tutti"] + sorted(df["sector"].unique().tolist()) if "sector" in df.columns else ["Tutti"]
            filter_sector = st.selectbox("Filtra per settore", sectors)
        with col3:
            pass

        year_val = int(filter_year) if filter_year != "Tutti" else None
        sector_val = filter_sector if filter_sector != "Tutti" else None

        agg = aggregate_results(results, filter_year=year_val, filter_sector=sector_val)

        # KPI
        st.markdown("### KPI")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Eventi analizzati", agg["total_analyzed"])
        m2.metric("Trade eseguiti", agg["total_trades"])
        m3.metric("Win", agg["wins"])
        m4.metric("Loss", agg["losses"])
        m5.metric("Win Rate", f"{agg['win_rate']}%")

        st.metric("Capitale totale generato (P&L)", f"${agg['total_pnl']:,.2f}")

        st.markdown("### Dettaglio per trade")
        filtered_df = df.copy()
        if year_val:
            filtered_df = filtered_df[filtered_df["year"] == year_val]
        if sector_val:
            filtered_df = filtered_df[filtered_df["sector"] == sector_val]
        st.dataframe(filtered_df, use_container_width=True)

with tab3:
    st.markdown("""
    ### Come funziona
    1. **Data Ingestion**: Scarica la lista di ticker (S&P500 o Nasdaq100) e tutti gli earnings storici dal Nasdaq API.
    2. **Simulation Loop**: Per ogni evento earnings, invoca la logica del bot (Earning Report Genius). Se il bot dice BUY, simula l'acquisto al prezzo del giorno e la vendita al prezzo del giorno successivo.
    3. **Output**: Win Rate, P&L totale, filtri per anno e settore.

    ### Bot Logic Placeholder
    Il file `backtest_engine.py` contiene `bot_logic_placeholder()` che implementa euristiche semplificate:
    - Run-up > 10% nelle ultime 2 settimane → NO_GO
    - Run-up < 5% → BUY
    - Fear dip (run-up negativo) → BUY

    Sostituisci questa funzione con la tua logica completa (es. integrazione Gemini) in `backtest_engine.py`.
    """)
