# ==========================================================
# MODELES.PY - Fonctions de modélisation pour le dashboard
# ==========================================================

import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from pmdarima import auto_arima
import warnings
warnings.filterwarnings('ignore')

    
    
def entrainer_sarima(series, horizon=8):
    """
    Entraîne un modèle SARIMA sur la série et retourne les prévisions
    
    PARAMÈTRES:
    -----------
    series : pd.Series
        Série temporelle de Nb_Cas
    horizon : int
        Nombre de semaines à prévoir
    
    RETOUR:
    -------
    dict avec forecast, lower, upper, order, seasonal_order
    """
    try:
        # Nettoyage
        series = pd.to_numeric(series, errors='coerce').dropna().sort_index()
        
        if len(series) < 15:
            return None
        
        # Gérer la fréquence
        try:
            freq = pd.infer_freq(series.index)
            if freq:
                series = series.asfreq(freq)
            else:
                series = series.reset_index(drop=True)
        except:
            series = series.reset_index(drop=True)
        
        series = series.dropna()
        
        # Entraîner SARIMA sur TOUTE la série
        model_auto = auto_arima(
            series,
            start_p=0, start_q=0,
            max_p=2, max_q=2,
            seasonal=True, m=4,
            trace=False,
            error_action='ignore',
            suppress_warnings=True,
            stepwise=True
        )
        
        # Créer le modèle SARIMAX
        model = SARIMAX(
            series,
            order=model_auto.order,
            seasonal_order=model_auto.seasonal_order
        )
        model_fit = model.fit(disp=False)
        
        # Prévisions
        forecast_result = model_fit.get_forecast(steps=horizon)
        forecast = forecast_result.predicted_mean
        conf_int = forecast_result.conf_int(alpha=0.05)  # IC 95%
        
        # Extraire les valeurs
        forecast_values = forecast.values
        lower_values = np.maximum(0, conf_int.iloc[:, 0].values)
        upper_values = conf_int.iloc[:, 1].values
        
        # Dates futures
        last_date = series.index[-1]
        if isinstance(last_date, pd.Timestamp):
            future_dates = pd.date_range(
                start=last_date + pd.Timedelta(days=7),
                periods=horizon,
                freq='W'
            )
        else:
            future_dates = pd.date_range(
                start=pd.Timestamp.now(),
                periods=horizon,
                freq='W'
            )
        
        return {
            'forecast': forecast_values,
            'lower': lower_values,
            'upper': upper_values,
            'dates': future_dates,
            'order': model_auto.order,
            'seasonal_order': model_auto.seasonal_order,
            'aic': model_fit.aic
        }
        
    except Exception as e:
        print(f"Erreur SARIMA: {e}")
        return None

def entrainer_sarima_lisse(series, horizon=8, alpha=0.7):
    """
    SARIMA avec lissage vers la moyenne historique
    Évite les prévisions trop faibles quand la tendance est extrême
    """
    resultats = entrainer_sarima(series, horizon)
    
    if resultats is None:
        return None
    
    # Moyenne historique
    moyenne = series.mean()
    
    # Lissage : mélange SARIMA et moyenne
    forecast_lisse = alpha * resultats['forecast'] + (1 - alpha) * moyenne
    
    # Ajuster l'IC
    lower = np.minimum(resultats['lower'], forecast_lisse)
    upper = np.maximum(resultats['upper'], forecast_lisse)
    
    return {
        'forecast': forecast_lisse,
        'lower': lower,
        'upper': upper,
        'dates': resultats['dates'],
        'order': resultats['order'],
        'seasonal_order': resultats['seasonal_order'],
        'aic': resultats['aic']
    }


def entrainer_prophet(series, horizon=8):
    """
    Entraîne Prophet et retourne les prévisions
    """
    try:
        from prophet import Prophet
        import logging
        logging.getLogger('prophet').setLevel(logging.WARNING)
        logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
        
        # Préparer les données
        df_prophet = pd.DataFrame({
            'ds': pd.to_datetime(series.index),
            'y': pd.to_numeric(series.values, errors='coerce')
        }).dropna()
        
        if len(df_prophet) < 10:
            return None
        
        # Modèle Prophet
        model = Prophet(
            growth='linear',
            yearly_seasonality='auto',
            weekly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode='additive',
            interval_width=0.95
        )
        model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
        
        # Entraîner
        model.fit(df_prophet)
        
        # Prévisions
        future = model.make_future_dataframe(periods=horizon, freq='W')
        forecast = model.predict(future)
        
        # Extraire les prévisions futures
        forecast_future = forecast.tail(horizon)
        
        return {
            'forecast': forecast_future['yhat'].values,
            'lower': forecast_future['yhat_lower'].values,
            'upper': forecast_future['yhat_upper'].values,
            'dates': forecast_future['ds'].values,
            'model': model
        }
        
    except Exception as e:
        print(f"Erreur Prophet: {e}")
        return None