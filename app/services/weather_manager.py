import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from datetime import date, timedelta
from typing import Dict, Any

class WeatherManager:
    def __init__(self):
        self.cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
        self.retry_session = retry(self.cache_session, retries = 5, backoff_factor = 0.2)
        self.openmeteo = openmeteo_requests.Client(session = self.retry_session)
        self.url = "https://api.open-meteo.com/v1/forecast"

    def get_weather_data(self, lat: float, lon: float, start_date: date, end_date: date) -> pd.DataFrame:
        """
        Busca dados do Open-Meteo para o intervalo solicitado.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "daily": ["precipitation_sum", "et0_fao_evapotranspiration"],
            "hourly": ["soil_moisture_0_to_7cm", "soil_temperature_0_to_7cm", "cloud_cover"],
            "timezone": "America/Sao_Paulo"
        }
        
        responses = self.openmeteo.weather_api(self.url, params=params)
        response = responses[0]
        
        # Process daily data
        daily = response.Daily()
        daily_data = {
            "date": pd.date_range(
                start = pd.to_datetime(daily.Time(), unit = "s", utc = True).tz_convert("America/Sao_Paulo"),
                end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True).tz_convert("America/Sao_Paulo"),
                freq = pd.Timedelta(seconds = daily.Interval()),
                inclusive = "left"
            ).date
        }
        daily_data["precipitation_sum"] = daily.Variables(0).ValuesAsNumpy()
        daily_data["et0_fao_evapotranspiration"] = daily.Variables(1).ValuesAsNumpy()
        
        df_daily = pd.DataFrame(data = daily_data)
        
        # Process hourly data
        hourly = response.Hourly()
        hourly_data = {
            "date": pd.date_range(
                start = pd.to_datetime(hourly.Time(), unit = "s", utc = True).tz_convert("America/Sao_Paulo"),
                end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True).tz_convert("America/Sao_Paulo"),
                freq = pd.Timedelta(seconds = hourly.Interval()),
                inclusive = "left"
            )
        }
        hourly_data["soil_moisture"] = hourly.Variables(0).ValuesAsNumpy()
        
        df_hourly = pd.DataFrame(data = hourly_data)
        df_hourly["date_only"] = df_hourly["date"].dt.date
        df_daily_moisture = df_hourly.groupby("date_only")["soil_moisture"].mean().reset_index()
        df_daily_moisture.columns = ["date", "satellite_soil_moisture"]
        
        # Merge
        df_final = pd.merge(df_daily, df_daily_moisture, on="date", how="left")
        
        return df_final
