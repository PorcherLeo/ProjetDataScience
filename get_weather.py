import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# codes recuperes sur site
code_weather = {
	"0": "Clear sky",
	"1": "Mainly clear",
	"2": "Partly cloudy",
	"3": "Overcast",
	"45": "Fog",
	"48": "Depositing rime fog",
	"51": "Light drizzle",
	"53": "Moderate drizzle",
	"55": "Dense drizzle",
	"56": "Light freezing drizzle",
	"57": "Dense freezing drizzle",
	"61": "Slight rain",
	"63": "Moderate rain",
	"65": "Heavy rain",
	"66": "Light freezing rain",
	"67": "Heavy freezing rain",
	"71": "Slight snowfall",
	"73": "Moderate snowfall",
	"75": "Heavy snowfall",
	"77": "Snow grains",
	"80": "Slight rain showers",
	"81": "Moderate rain showers",
	"82": "Violent rain showers",
	"85": "Slight snow showers",
	"86": "Heavy snow showers",
	"95": "Thunderstorm",
	"96": "Thunderstorm with slight hail",
	"97": "Heavy thunderstorm",
	"99": "Thunderstorm with heavy hail"
}

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 48.8534,
	"longitude": 2.3488,
	"daily": "weather_code",
	"hourly": ["temperature_2m", "weather_code", "rain", "precipitation", "apparent_temperature", "wind_speed_10m"],
	"minutely_15": ["temperature_2m", "apparent_temperature", "precipitation", "weather_code", "wind_speed_10m", "rain"],
	"start_date": "2026-10-16",
	"end_date": "2026-10-25",
}
responses = openmeteo.weather_api(url, params = params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation: {response.Elevation()} m asl")
print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

# Process minutely_15 data. The order of variables needs to be the same as requested.
minutely_15 = response.Minutely15()
minutely_15_temperature_2m = minutely_15.Variables(0).ValuesAsNumpy()
minutely_15_apparent_temperature = minutely_15.Variables(1).ValuesAsNumpy()
minutely_15_precipitation = minutely_15.Variables(2).ValuesAsNumpy()
minutely_15_weather_code = minutely_15.Variables(3).ValuesAsNumpy()
minutely_15_wind_speed_10m = minutely_15.Variables(4).ValuesAsNumpy()
minutely_15_rain = minutely_15.Variables(5).ValuesAsNumpy()

minutely_15_data = {
	"date": pd.date_range(
		start = pd.to_datetime(minutely_15.Time(), unit = "s", utc = True),
		end =  pd.to_datetime(minutely_15.TimeEnd(), unit = "s", utc = True),
		freq = pd.Timedelta(seconds = minutely_15.Interval()),
		inclusive = "left"
	)
}

minutely_15_data["temperature_2m"] = minutely_15_temperature_2m
minutely_15_data["apparent_temperature"] = minutely_15_apparent_temperature
minutely_15_data["precipitation"] = minutely_15_precipitation
minutely_15_data["weather_code"] = minutely_15_weather_code
minutely_15_data["wind_speed_10m"] = minutely_15_wind_speed_10m
minutely_15_data["rain"] = minutely_15_rain

# Convertir les clés du dictionnaire en entiers
weather_labels = {int(code): label for code, label in code_weather.items()}

minutely_15_dataframe = pd.DataFrame(data = minutely_15_data)

minutely_15_dataframe["weather_label"] = (
    minutely_15_dataframe["weather_code"]
    .map(weather_labels)
    .fillna("Unknown")
)

# Exporter sans l'index pandas
minutely_15_dataframe.to_csv(
    "meteo_paris_octobre_2026.csv",
    index=False,
    encoding="utf-8-sig"
)

# print(minutely_15_dataframe.head())

# print("\nMinutely15 data\n", minutely_15_dataframe)
