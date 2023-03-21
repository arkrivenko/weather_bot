from security import WEATHER_KEY, GEO_KEY, TOKEN
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import requests

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class UserState(StatesGroup):
    city = State()


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
    button1 = types.KeyboardButton("Погода по геолокации 🧭", request_location=True)
    button2 = types.KeyboardButton("Погода на ближайшие 3 дня")
    keyboard.add(button1).add(button2)
    await message.answer("Для отображения прогноза погоды введите свой город 🏠,\n"
                         "либо нажмите на кнопку передачи геолокации 🧭\n", reply_markup=keyboard)


@dp.message_handler(content_types=['location'])
async def get_geo(message: types.Message):
    lat = message.location.latitude
    lon = message.location.longitude
    await get_weather_data(lat, lon, message)


@dp.message_handler(Text(equals='Погода на ближайшие 3 дня'))
async def weather_now(message: types.Message):
    await message.answer("Введите свой населенный пункт")
    await UserState.city.set()


@dp.message_handler(state=UserState.city)
async def city_set(message: types.Message, state: FSMContext):
    if not message.text:
        return
    await state.update_data(city=message.text)
    user_data = await state.get_data()
    city = user_data.get("city")
    await state.finish()
    lat, lon = await get_city_geo(city)
    await get_full_weather_data(lat, lon, message)


@dp.message_handler(content_types=['text'])
async def city_input(message: types.Message):
    try:
        city = message.text.strip().lower()
        lat, lon = await get_city_geo(city)
        await get_weather_data(lat, lon, message)
    except Exception as ex:
        print(f"Ошибка внутри city_input:\n{ex}")


async def get_city_geo(city):
    url = f"https://geocode-maps.yandex.ru/1.x/?apikey={GEO_KEY}&geocode={city}&format=json"

    try:
        response = requests.get(url)
        response_data = response.json()
        coordinates = response_data.get("response").get("GeoObjectCollection"). \
            get("featureMember")[0].get("GeoObject").get("Point").get("pos").split()
        lat = coordinates[1]
        lon = coordinates[0]
        return lat, lon

    except Exception as ex:
        print(f"Ошибка внутри get_city_geo:\n{ex}")


async def get_weather_data(lat, lon, message):
    headers = {"X-Yandex-API-Key": WEATHER_KEY}
    url = f"https://api.weather.yandex.ru/v2/forecast?lat={lat}&lon={lon}&limit=1"

    try:
        response = requests.get(url, headers=headers)
        weather_data = response.json()
        fact = weather_data.get("fact")
        temp = fact.get("temp")
        status = fact.get("condition")
        feels_like = fact.get("feels_like")
        forecasts = weather_data.get("forecasts")[0]
        sunset, rise_begin, parts, morning, morning_temp, morning_wind_speed, morning_status, day, day_temp, \
            day_wind_speed, day_status, evening, evening_temp, evening_wind_speed, evening_status, night, night_temp, \
            night_wind_speed, night_status = await get_forecast_data(forecasts)
        await message.answer(f"Температура: <b>{temp}°C</b>, ощущается как <b>{feels_like}°C</b>\n"
                             f"<em>{weather_status.get(status).title()}\n</em>"
                             f"\nвосход🌅 - <b>{rise_begin}</b>, закат🌆 - <b>{sunset}</b>\n"
                             f"\n<em>Утро</em>🌇 ({morning_status}):\nтемпература🌡️ - <b>{morning_temp}°C</b>, "
                             f"скорость ветра🌬️ - <b>{morning_wind_speed}м/с</b>\n"
                             f"\n<em>День</em>🏘️ ({day_status}):\nтемпература🌡️ - <b>{day_temp}°C</b>, "
                             f"скорость ветра🌬️ - <b>{day_wind_speed}м/с</b>\n"
                             f"\n<em>Вечер</em>🌆 ({evening_status}):\nтемпература🌡️ - <b>{evening_temp}°C</b>, "
                             f"скорость ветра🌬️ - <b>{evening_wind_speed}м/с</b>\n"
                             f"\n<em>Ночь</em>🏙️ ({night_status}):\nтемпература🌡️ - <b>{night_temp}°C</b>, "
                             f"скорость ветра🌬️ - <b>{night_wind_speed}м/с</b>\n", parse_mode="html")

    except Exception as ex:
        print(f"Ошибка внутри get_weather_data:\n{ex}")


async def get_full_weather_data(lat, lon, message):
    headers = {"X-Yandex-API-Key": WEATHER_KEY}
    url = f"https://api.weather.yandex.ru/v2/forecast?lat={lat}&lon={lon}&limit=4"

    try:
        response = requests.get(url, headers=headers)
        weather_data = response.json()
        forecasts = weather_data.get("forecasts")
        for elem in forecasts[1:]:
            date = elem.get("date")
            sunset, rise_begin, parts, morning, morning_temp, morning_wind_speed, morning_status, day, day_temp, \
                day_wind_speed, day_status, evening, evening_temp, evening_wind_speed, evening_status, night, \
                night_temp, night_wind_speed, night_status = await get_forecast_data(elem)
            await message.answer(f"Прогноз на <b><ins>{date}</ins></b>:\nвосход🌅 - <b>{rise_begin}</b>, "
                                 f"закат🌆 - <b>{sunset}</b>\n"
                                 f"\n<em>Утро</em>🌇 ({morning_status}):\nтемпература🌡️ - <b>{morning_temp}°C</b>, "
                                 f"скорость ветра🌬️ - <b>{morning_wind_speed}м/с</b>\n"
                                 f"\n<em>День</em>🏘️ ({day_status}):\nтемпература🌡️ - <b>{day_temp}°C</b>, "
                                 f"скорость ветра🌬️ - <b>{day_wind_speed}м/с</b>\n"
                                 f"\n<em>Вечер</em>🌆 ({evening_status}):\nтемпература🌡️ - <b>{evening_temp}°C</b>, "
                                 f"скорость ветра🌬️ - <b>{evening_wind_speed}м/с</b>\n"
                                 f"\n<em>Ночь</em>🏙️ ({night_status}):\nтемпература🌡️ - <b>{night_temp}°C</b>, "
                                 f"скорость ветра🌬️ - <b>{night_wind_speed}м/с</b>\n", parse_mode="html")
    except Exception as ex:
        print(f"Ошибка внутри get_full_weather_data:\n{ex}")


async def get_forecast_data(forecasts):
    sunset = forecasts.get("sunset")
    rise_begin = forecasts.get("rise_begin")
    parts = forecasts.get("parts")
    morning = parts.get("morning")
    morning_temp = morning.get("temp_avg")
    morning_wind_speed = morning.get("wind_speed")
    morning_status = weather_status.get(morning.get("condition"))
    day = parts.get("day")
    day_temp = day.get("temp_avg")
    day_wind_speed = day.get("wind_speed")
    day_status = weather_status.get(day.get("condition"))
    evening = parts.get("evening")
    evening_temp = evening.get("temp_avg")
    evening_wind_speed = evening.get("wind_speed")
    evening_status = weather_status.get(evening.get("condition"))
    night = parts.get("night")
    night_temp = night.get("temp_avg")
    night_wind_speed = night.get("wind_speed")
    night_status = weather_status.get(night.get("condition"))
    return sunset, rise_begin, parts, morning, morning_temp, morning_wind_speed, morning_status, day, day_temp, \
        day_wind_speed, day_status, evening, evening_temp, evening_wind_speed, evening_status, night, night_temp, \
        night_wind_speed, night_status


def main():
    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    main()
