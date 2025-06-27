import httpx
from config import env

OPENWEATHER_API_KEY = env("OPENWEATHER_API_KEY")
LATITUDE = "32.33"
LONGITUDE = "-6.35"


def check_weather_before_irrigation():
    """
    Fonction SYNCHRONE pour récupérer la quantité de pluie prévue dans les 24 prochaines heures.
    Utilisée par le scheduler pour les notifications.
    """
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LATITUDE}&lon={LONGITUDE}&appid={OPENWEATHER_API_KEY}&units=metric"

    try:
        response = httpx.get(url)
        if response.status_code != 200:
            return 0

        data = response.json()
        rain_total = 0.0

        # Prendre les 8 premières prévisions (chaque 3h = 24h)
        for forecast in data["list"][:8]:
            if "rain" in forecast and "3h" in forecast["rain"]:
                rain_total += forecast["rain"]["3h"]

        return rain_total

    except Exception as e:
        print(f"Erreur lors de la récupération de la météo : {e}")
        return 0


