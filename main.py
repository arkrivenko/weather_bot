from security import WEATHER_KEY, GEO_KEY, TOKEN
from aiogram import Bot, Dispatcher, executor, types
import requests

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
weather_status = {
    "clear": "ясно",
    "partly-cloudy": "малооблачно",
    "cloudy": "облачно с прояснениями",
    "overcast": "пасмурно",
    "drizzle": "морось",
    "light-rain": "небольшой дождь",
    "rain": "дождь",
    "moderate-rain": "умеренно сильный дождь",
    "heavy-rain": "сильный дождь",
    "continuous-heavy-rain": "длительный сильный дождь",
    "showers": "ливень",
    "wet-snow": "дождь со снегом",
    "light-snow": "небольшой снег",
    "snow": "снег",
    "snow-showers": "снегопад",
    "hail": "град",
    "thunderstorm": "гроза",
    "thunderstorm-with-rain": "дождь с грозой",
    "thunderstorm-with-hail": "гроза с градом",
}


@dp.message_handler(commands='start')
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton("🧭", request_location=True)
    keyboard.add(button)
    await message.answer("Для отображения прогноза погоды введите свой город 🏠\n"
                         "Либо нажмите на кнопку передачи геолокации 🧭", reply_markup=keyboard)


@dp.message_handler(content_types=['location'])
async def get_geo(message: types.Message):
    lat = message.location.latitude
    lon = message.location.longitude
    await get_weather_data(lat, lon, message)


@dp.message_handler(content_types=['text'])
async def city_input(message: types.Message):
    city = message.text.strip().lower()
    url = f"https://geocode-maps.yandex.ru/1.x/?apikey={GEO_KEY}&geocode={city}&format=json"

    try:
        response = requests.get(url)
        response_data = response.json()
        coordinates = response_data.get("response").get("GeoObjectCollection").\
            get("featureMember")[0].get("GeoObject").get("Point").get("pos").split()
        lat = coordinates[1]
        lon = coordinates[0]
        await get_weather_data(lat, lon, message)

    except Exception as ex:
        await message.answer("Что-то пошло не так..")


async def get_weather_data(lat, lon, message):
    headers = {"X-Yandex-API-Key": WEATHER_KEY}
    url = f"https://api.weather.yandex.ru/v2/forecast?lat={lat}&lon={lon}"

    try:
        response = requests.get(url, headers=headers)
        weather_data = response.json()
        fact = weather_data.get("fact")
        temp = fact.get("temp")
        status = fact.get("condition")
        feels_like = fact.get("feels_like")
        await message.answer(f"Температура: {temp}°C, ощущается как {feels_like}°C\n"
                             f"{weather_status.get(status).title()}")

    except Exception as ex:
        message.answer("Что-то пошло не так..")


def main():
    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    main()
