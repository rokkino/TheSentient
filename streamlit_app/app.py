"""
TheSentient - Dashboard Backtesting (Streamlit)
Simulazione storica su dati earnings (S&P 500 / Nasdaq).
"""
import streamlit as st
import pandas as pd
import requests
import time
import json
from datetime import datetime

# Configuration
API_URL = "http://127.0.0.1:8000/api"

st.set_page_config(page_title="Backtesting – TheSentient", page_icon="📊", layout="wide")

# Parametri da frontend (selettore bot e data)
try:
    _qp = getattr(st, "query_params", None) or st.experimental_get_query_params()
    _bot_id = _qp.get("bot_id", [None])[0] if isinstance(_qp.get("bot_id"), list) else _qp.get("bot_id")
    _date_param = _qp.get("date", [None])[0] if isinstance(_qp.get("date"), list) else _qp.get("date")
except Exception:
    _bot_id = None
    _date_param = None

st.title("Backtesting – Simulazione earnings")
st.markdown("*Simulazione storica su dati earnings (backend-powered).*")

# Helper functions
def get_active_backtests():
    try:
        resp = requests.get(f"{API_URL}/backtest/active", timeout=2)
        if resp.status_code == 200:
            return resp.json().get("active_jobs", [])
        return []
    except:
        return []

def get_backtest_status(job_id):
    try:
        resp = requests.get(f"{API_URL}/backtest/status/{job_id}", timeout=2)
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None

# Sidebar: Configurazione
with st.sidebar:
    st.header("⚙️ Configurazione")

    universe = st.selectbox("Universo ticker", ["S&P 500", "Nasdaq 100"], index=0)
    
    start_year = st.number_input("Anno inizio", 2015, 2026, 2024)
    end_year = st.number_input("Anno fine", 2015, 2026, 2024)
    
    if start_year > end_year:
        st.error("Anno inizio deve essere ≤ anno fine")
        st.stop()

    capital_per_trade = st.number_input("Capitale per trade ($)", 100, 10000, 1000)
    min_confidence = st.slider("Confidence minima bot (%)", 0, 80, 30)
    
    limit_tickers = st.number_input("Limite Tickers (0 = tutti)", 0, 500, 50)
    
    st.divider()
    st.caption("Strategy: Buy day before earnings (Pre-market) or day of earnings (Post-market). Sell next open.")

# Initialize session state for job tracking
if "job_id" not in st.session_state:
    st.session_state["job_id"] = None
    
# Check for existing active jobs on load
if not st.session_state["job_id"]:
    active = get_active_backtests()
    if active:
        # Auto-attach to the most recent one
        latest = active[-1]
        st.session_state["job_id"] = latest["id"]
        st.toast(f"Reconnected to running job {latest['id']}")

# Tab principale
tab1, tab2, tab3 = st.tabs(["▶️ Esegui Backtest", "📈 Report", "ℹ️ Info"])

with tab1:
    st.subheader("Avvia simulazione")
    
    # Run Button
    if not st.session_state["job_id"]:
        if st.button("🚀 Avvia Backtest (Backend)", type="primary"):
            try:
                payload = {
                    "universe": universe,
                    "start_year": start_year,
                    "end_year": end_year,
                    "capital": float(capital_per_trade),
                    "min_confidence": min_confidence,
                    "limit": limit_tickers if limit_tickers > 0 else None
                }
                resp = requests.post(f"{API_URL}/backtest/run", json=payload, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state["job_id"] = data["job_id"]
                    st.rerun()
                else:
                    st.error(f"Failed to start backtest: {resp.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")
    else:
        if st.button("🛑 Stop / Nuova simulazione"):
            st.session_state["job_id"] = None
            st.rerun()

    # Progress Area
    if st.session_state["job_id"]:
        job_id = st.session_state["job_id"]
        status_placeholder = st.empty()
        progress_bar = st.progress(0)
        log_placeholder = st.empty()
        
        # Polling loop
        while True:
            status = get_backtest_status(job_id)
            if not status:
                st.error("Lost connection to job or job not found.")
                st.session_state["job_id"] = None
                break
                
            state = status.get("status")
            pct = status.get("progress", 0.0)
            msg = status.get("message", "")
            
            progress_bar.progress(min(pct, 1.0), text=f"{state}: {int(pct*100)}%")
            status_placeholder.info(f"Status: **{state}**")
            log_placeholder.code(msg)
            
            if state in ["COMPLETED", "FAILED"]:
                if state == "COMPLETED":
                    st.success("Backtest Completed!")
                    st.session_state["results"] = status.get("results")
                    st.session_state["stats"] = status.get("stats")
                else:
                    st.error(f"Backtest Failed: {msg}")
                
                st.session_state["job_id"] = None # Reset job so we can run again
                time.sleep(2)
                st.rerun()
                break
            
            time.sleep(1)

with tab2:
    st.subheader("Report aggregato")
    if "results" not in st.session_state:
        st.info("Nessun risultato disponibile.")
    else:
        results = st.session_state["results"]
        stats = st.session_state.get("stats", {})
        
        # Stats Header
        if stats:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Trades", stats.get("total_trades"))
            c2.metric("Win Rate", f"{stats.get('win_rate')}%")
            c3.metric("Total P&L", f"${stats.get('total_pnl')}")
            c4.metric("Best Trade", f"${stats.get('best_trade')}")
            
        df = pd.DataFrame(results)
        
        if not df.empty:
            # Filters
            sectors = ["All"] + sorted(list(set(df["sector"].astype(str))))
            sel_sector = st.selectbox("Filter by Sector", sectors)
            
            filtered_df = df if sel_sector == "All" else df[df["sector"] == sel_sector]
            
            st.dataframe(filtered_df, use_container_width=True)
            
            # Simple Chart of PnL
            st.line_chart(filtered_df["pnl"].cumsum())

with tab3:
    st.markdown("""
    ### Backend Powered Backtesting
    
    The trading logic now runs on the backend server, ensuring that long-running simulations
    continue even if you close or reload this page.
    
    ### Strategy
    - **Pre-Market Earnings**: Buy Close (Day before) -> Sell Open (Day of earnings)
    - **Post-Market Earnings**: Buy Close (Day of earnings) -> Sell Open (Day after)
    
    ### Sectors
    - **Biomedical** (Healthcare)
    - **Engineering** (Industrials)
    - **Technology** (Technology)
    """)
