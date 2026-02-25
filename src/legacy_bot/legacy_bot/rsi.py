import pandas as pd
import mplfinance as mpf

def calculate_rsi(data, period=14):
    """
    Calcola il Relative Strength Index (RSI) usando pandas.
    """
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_rsi_plot(data, ax_indicator):
    """
    Calcola l'RSI e prepara i dizionari addplot per mplfinance
    usando la modalità Assi Esterni.
    
    Args:
        data (pd.DataFrame): Il dataframe OHLCV (verrà modificato).
        ax_indicator (matplotlib.axis.Axes): L'asse su cui disegnare l'RSI.

    Returns:
        list: Una lista di dizionari 'addplot'.
    """
    
    # Calcola l'RSI e aggiungilo al dataframe (questo lo modifica)
    data['RSI'] = calculate_rsi(data)
    
    # Prepara i plot
    rsi_plots = [
        # La linea RSI principale
        mpf.make_addplot(data['RSI'], 
                         ax=ax_indicator, # <-- MODIFICATO: da panel= a ax=
                         color='cyan', 
                         ylabel=f'RSI(14)', 
                         secondary_y=False),
        
        # Linea ipercomprato (70)
        mpf.make_addplot(pd.Series(70, index=data.index), 
                         ax=ax_indicator, # <-- MODIFICATO
                         color='#e05757', # Rosso
                         linestyle='--', 
                         alpha=0.7, 
                         secondary_y=False),
        
        # Linea ipervenduto (30)
        mpf.make_addplot(pd.Series(30, index=data.index), 
                         ax=ax_indicator, # <-- MODIFICATO
                         color='#57e057', # Verde
                         linestyle='--', 
                         alpha=0.7, 
                         secondary_y=False)
    ]
    
    return rsi_plots