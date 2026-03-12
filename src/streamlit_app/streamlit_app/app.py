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
API_URL = "http://127.0.0.1:8001/api"

# Read query params (passed from Vue frontend when embedded)
def get_param(key, default=None):
    try:
        if hasattr(st, "query_params"):
            return st.query_params.get(key, default)
        else:
            val = st.experimental_get_query_params().get(key, default)
            if isinstance(val, list) and len(val) > 0:
                return val[0]
            return default
    except:
        return default

_bot_id = get_param("bot_id")
_date_param = get_param("date")
universe = get_param("universe") or "S&P 500"
start_year = int(get_param("start_year") or 2024)
end_year = int(get_param("end_year") or 2024)
capital_per_trade = int(get_param("capital") or 1000)
min_confidence = int(get_param("min_confidence") or 30)
limit_tickers = int(get_param("limit") or 50)

st.set_page_config(page_title="Backtesting – TheSentient", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")
# Hide sidebar completely via CSS
st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

st.title("Backtesting – Simulazione earnings")
st.markdown("*Simulazione storica su dati earnings (backend-powered).*")

# Helper functions
def get_recent_backtests():
    try:
        resp = requests.get(f"{API_URL}/backtest/recent", timeout=2)
        if resp.status_code == 200:
            return resp.json().get("recent_jobs", [])
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

# Inject JS listener for dynamic config updates from Vue via postMessage
st.markdown("""
<script>
window.addEventListener('message', function(event) {
    if (event.data && event.data.type === 'updateBacktestConfig') {
        const cfg = event.data.config;
        const params = new URLSearchParams(window.location.search);
        if (cfg.universe !== undefined) params.set('universe', cfg.universe);
        if (cfg.start_year !== undefined) params.set('start_year', String(cfg.start_year));
        if (cfg.end_year !== undefined) params.set('end_year', String(cfg.end_year));
        if (cfg.capital !== undefined) params.set('capital', String(cfg.capital));
        if (cfg.min_confidence !== undefined) params.set('min_confidence', String(cfg.min_confidence));
        if (cfg.limit !== undefined) params.set('limit', String(cfg.limit));
        if (cfg.bot_id !== undefined) params.set('bot_id', String(cfg.bot_id));
        if (cfg.date !== undefined) params.set('date', cfg.date);
        const newUrl = window.location.pathname + '?' + params.toString();
        window.history.replaceState({}, '', newUrl);
        // Trigger Streamlit rerun by dispatching a custom event
        window.dispatchEvent(new Event('streamlit:rerun'));
    }
});
</script>
""", unsafe_allow_html=True)

# Validate years
if start_year > end_year:
    st.error("Anno inizio deve essere ≤ anno fine")
    st.stop()

# Initialize session state for job tracking
if "job_id" not in st.session_state:
    st.session_state["job_id"] = None
    
# Check for existing recent jobs on load
if not st.session_state["job_id"]:
    recent = get_recent_backtests()
    if recent:
        # Auto-attach to the most recent one (sorted descending by started_at)
        latest = recent[0]
        if latest["status"] in ["STARTING", "RUNNING"]:
            st.session_state["job_id"] = latest["id"]
            st.toast(f"Reconnected to running job {latest['id']}")
        elif latest["status"] == "COMPLETED" and "results" not in st.session_state:
            # If the backend has a completed job and we have no results, load them
            st.session_state["results"] = latest.get("results")
            st.session_state["stats"] = latest.get("stats")
            st.toast("Loaded recent backtest results.")

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
        
        # Status Check (Single pull + rerun)
        status = get_backtest_status(job_id)
        if not status:
            st.error("Lost connection to job or job not found.")
            st.session_state["job_id"] = None
            st.rerun()
            
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
            time.sleep(0.5)
            st.toast("Puoi visualizzare i risultati nella tab Report.")
            st.rerun() # Force rerun so the Report tab recognizes the updated state immediately
        else:
            time.sleep(1)
            st.rerun()

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
            
            if not filtered_df.empty:
                st.dataframe(filtered_df, use_container_width=True)
                
                # Simple Chart of PnL
                if "pnl" in filtered_df.columns:
                    st.line_chart(filtered_df["pnl"].cumsum())
            else:
                st.warning(f"Nessun trade trovato per il settore {sel_sector}.")
        else:
            st.warning("Il backtest non ha prodotto alcun trade con questi parametri.")

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
