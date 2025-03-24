# Приклад 1: API-запити (Об’єктний адаптер)

# Код без адаптера (ручне перетворення)
import requests  

class OldWeatherAPI:
    """Старий API повертає температуру у градусах Цельсія"""
    def get_temperature(self, city):
        # Імітуємо запит до API, яке повертає температуру в °C
        print(f"Fetching weather data for {city}...")
        return {"city": city, "temperature": 20}  # 20°C

class WeatherApp:
    """Додаток, який очікує температуру у Фаренгейтах"""
    def display_temperature(self, temperature_fahrenheit):
        print(f"Current temperature in {temperature_fahrenheit}°F")

# Використання без адаптера (ручне перетворення)
old_api = OldWeatherAPI()
weather_app = WeatherApp()

data = old_api.get_temperature("Kyiv")  # Отримуємо температуру в °C
temperature_celsius = data["temperature"]
temperature_fahrenheit = (temperature_celsius * 9/5) + 32  # Ручне перетворення

weather_app.display_temperature(temperature_fahrenheit)  # Ручна конвертація


# Код з об’єктним адаптером (автоматична конвертація)
import requests 

class OldWeatherAPI:
    """Старий API повертає температуру у градусах Цельсія"""
    def get_temperature(self, city):
        print(f"Fetching weather data for {city}...")
        return {"city": city, "temperature": 20}  # 20°C

class WeatherAdapter:
    """Адаптер, який конвертує температуру в потрібний формат"""
    def __init__(self, old_api):
        self.old_api = old_api  # Композиція (адаптер містить старий API)

    def get_temperature_fahrenheit(self, city):
        """Отримує температуру у Фаренгейтах"""
        data = self.old_api.get_temperature(city)
        celsius = data["temperature"]
        fahrenheit = (celsius * 9/5) + 32
        return {"city": city, "temperature": fahrenheit}

class WeatherApp:
    """Додаток, який очікує температуру у Фаренгейтах"""
    def display_temperature(self, temperature_fahrenheit):
        print(f"Current temperature in {temperature_fahrenheit}°F")

# Використання адаптера (автоматична конвертація)
old_api = OldWeatherAPI()
adapter = WeatherAdapter(old_api)  # Обгортаємо старий API адаптером
weather_app = WeatherApp()

data = adapter.get_temperature_fahrenheit("Kyiv")  # Отримуємо вже готові °F
weather_app.display_temperature(data["temperature"])  # Все працює автоматично
