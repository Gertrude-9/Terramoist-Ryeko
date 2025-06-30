import requests
from datetime import datetime, timedelta

def get_weather_forecast(city, api_key, days=5):
    """
    Fetches weather forecast data from OpenWeatherMap API
    and returns a daily summary for the next 'days' days.

    Args:
        city (str): City name (e.g., "London")
        api_key (str): Your OpenWeatherMap API key
        days (int): Number of days to forecast (max 5 with this API)

    Returns:
        list of dict: Each dict contains date, temp_max, temp_min, precipitation, cloud_cover, conditions, recommendation
        Returns an empty list if the API call or processing fails.
    """
    url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric'

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Check if 'list' key exists in response
        if 'list' not in data:
            print("Warning: 'list' key not in API response")
            return []

        # The forecast is every 3 hours for 5 days, group by day
        forecast_data = {}

        for entry in data['list']:
            dt_txt = entry.get('dt_txt')
            if not dt_txt:
                continue
            date_str = dt_txt.split(' ')[0]

            if date_str not in forecast_data:
                forecast_data[date_str] = {
                    'temp_max': entry['main']['temp_max'],
                    'temp_min': entry['main']['temp_min'],
                    'precipitation': 0,
                    'cloud_cover': entry['clouds']['all'],
                    'conditions_list': [],
                }
            else:
                # Update max and min temps
                forecast_data[date_str]['temp_max'] = max(forecast_data[date_str]['temp_max'], entry['main']['temp_max'])
                forecast_data[date_str]['temp_min'] = min(forecast_data[date_str]['temp_min'], entry['main']['temp_min'])
                # Sum precipitation (rain or snow)
                rain = entry.get('rain', {}).get('3h', 0)
                snow = entry.get('snow', {}).get('3h', 0)
                forecast_data[date_str]['precipitation'] += rain + snow
                # Update cloud cover to max value seen
                forecast_data[date_str]['cloud_cover'] = max(forecast_data[date_str]['cloud_cover'], entry['clouds']['all'])

            # Append weather conditions description
            weather_conditions = entry['weather'][0]['description']
            if weather_conditions not in forecast_data[date_str]['conditions_list']:
                forecast_data[date_str]['conditions_list'].append(weather_conditions)

        # Prepare final list limited to requested days
        forecast_list = []
        today = datetime.now().date()
        for i in range(days):
            day = today + timedelta(days=i)
            day_str = day.strftime('%Y-%m-%d')
            if day_str in forecast_data:
                day_data = forecast_data[day_str]
                # Create recommendation based on precipitation and cloud cover
                if day_data['precipitation'] > 1.0:
                    recommendation = 'Reduce irrigation due to expected rain.'
                elif day_data['cloud_cover'] > 70:
                    recommendation = 'Consider moderate irrigation; cloudy day.'
                else:
                    recommendation = 'Normal irrigation.'

                forecast_list.append({
                    'date': day_str,
                    'temp_max': round(day_data['temp_max'], 1),
                    'temp_min': round(day_data['temp_min'], 1),
                    'precipitation': round(day_data['precipitation'], 2),
                    'cloud_cover': day_data['cloud_cover'],
                    'conditions': ', '.join(day_data['conditions_list']),
                    'recommendation': recommendation,
                })

        return forecast_list

    except requests.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return []
    except Exception as e:
        print(f"Error processing weather data: {e}")
        return []

# Example usage:
if __name__ == "__main__":
    api_key = '03d758ad12df45f05330bc3d12f2f440'
    city = 'Kampala'

    forecast = get_weather_forecast(city, api_key, days=5)
    if not forecast:
        print("No forecast data available.")
    else:
        for day in forecast:
            print(day)
