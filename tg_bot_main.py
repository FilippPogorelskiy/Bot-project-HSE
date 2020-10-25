import re
import telebot
import configure
from tabulate import tabulate
from telebot.types import Message
from time import sleep
from selenium import webdriver as wb
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from bs4 import BeautifulSoup as bs
import os


token = os.environ['TOKEN']
bot = telebot.TeleBot(token)


# Функция получения городов для выбора
def get_town_name(town_input):
    global br
    global gismeteo_url
    #options = FirefoxOptions()
    #options.add_argument("--headless")
    #br = wb.Firefox(options=options)
    GOOGLE_CHROME_PATH = '/app/.apt/usr/bin/google_chrome'
    CHROMEDRIVER_PATH = '/app/.chromedriver/bin/chromedriver'
    chrome_options = wb.ChromeOptions()
    chrome_options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.binary_location = GOOGLE_CHROME_PATH
    br = wb.Chrome(executable_path=os.environ.get('CHROMEDRIVER_PATH'), chrome_options=chrome_options)
    gismeteo_url = 'https://www.gismeteo.ru'
    br.get(gismeteo_url)
    town_field = br.find_element_by_xpath('//*[@id="js-search"]')
    town_field.send_keys(town_input)
    sleep(4)
    town_page = br.page_source
    town_page_soup = bs(town_page, 'lxml')
    get_town_url = town_page_soup.find_all('a', attrs={r'data-type': "city"})
    if len(get_town_url) < 1:
        town_not_found = 'Город не найден'
        return town_not_found
    else:
        towns_url = []
        towns_name = []
        for i in get_town_url:
            twn_urls = i.get('href')
            twn_name = i.find_all('span')
            for _ in twn_name:
                town_list = [t.text for t in twn_name]
                town_key = ', '.join(town_list)
                town_key = town_key.replace('\n', '').replace('    ', '')
            towns_name.append(town_key)
            towns_url.append(gismeteo_url + twn_urls + '3-days/')
        town_url_dict = dict(zip(towns_name, towns_url))
    return town_url_dict


# Функция получения ссылок для выбора дня недели
def weather_for_week_urls(towns_url_input):
    br.get(towns_url_input)
    weather_page = br.page_source
    weather_soup = bs(weather_page, 'lxml')
    day_url = weather_soup.find_all('a', class_=['link blue', 'link weekend'])
    url_list = []
    for i in day_url[5:12]:
        day_url_get = i.get('href')
        url_list.append(gismeteo_url + day_url_get)
    return url_list


# Функция получения информации о погоде на конкретный день
def get_weather_info(week_day):
    descript_weather_list = []
    temp_weather_list = []
    rainfall = 0
    wind_list = []
    road_weather_list = []
    br.get(day_urls_for_town[week_day])
    sleep(0.5)
    day_weather = br.page_source
    sleep(0.5)
    day_weather_soup = bs(day_weather, 'lxml')
    date_weather_soup = day_weather_soup.find_all('div', class_='date')
    date_weather = re.sub('\W+', ' ', date_weather_soup[2].text).strip()
    for i in list(configure.month_day_dict.keys()):
        date_weather = date_weather.replace(i, configure.month_day_dict.get(i))
    descript_weather_soup = day_weather_soup.find_all('span', class_='tooltip')
    for t in descript_weather_soup:
        descript_weather_list.append(t.get("data-text"))
    for e in list(configure.emoji_dict.keys()):
        for d in range(len(descript_weather_list)):
            descript_weather_list[d] = descript_weather_list[d].replace(e, configure.emoji_dict.get(e))
    temp_weather_soup = day_weather_soup.find_all('span', class_='unit unit_temperature_c')
    for t in temp_weather_soup[6:]:
        temp_weather_list.append(t.text)
    rainfall_soup = day_weather_soup.find_all('div', class_='w_prec__value')
    for r in rainfall_soup:
        rainfall_value = float(r.text.strip().replace('н/д', '0').replace(',', '.'))
        rainfall = round((rainfall + rainfall_value), 1)
    wind_soup = day_weather_soup.find_all('div',
                                          attrs={r'data-widget-id': "wind"})[0].find_all('span',
                                                                                         class_='unit unit_wind_m_s')
    for t in wind_soup[9:]:
        wind_list.append(int(t.text.strip().replace('—', '0')))
    road_weather_soup = day_weather_soup.find_all('div', class_='w_roadcondition__description')
    for t in road_weather_soup:
        road_weather_list.append(t.text.strip())
    return date_weather, descript_weather_list, temp_weather_list, rainfall, wind_list, road_weather_list


@bot.message_handler(commands=["info"])
def cmd_info(message):
    bot.send_message(message.chat.id, f"Я знаю о погоде во всем мире.{configure.earth}\n"
                                      "Для того, чтобы узнать погоду напишите наименование "
                                      "города после команды /town.\n"
                                      "Следует писать без знаков препинания.\n"
                                      "Я умею распознавать города на английском языке.\n"
                                      "Если перепутаете раскладку языка - ничего страшного, "
                                      f"я и это распознаю.{configure.winking_face}\n"
                                      "Для уточнения можно указать область или страну\n\n"
                                      f"После того, как введете город, появится уточняющий список."
                                      f"Из появившегося списка скопируйте и вставьте в строку то, "
                                      f"что Вам нужно.{configure.smile_face}\n"
                                      f"Если введете произвольный набор букв, "
                                      f"по-умолчанию произведется выбор первого города из списка.\n\n"
                                      f"Далее, нужно выбрать день, "
                                      f"на который вы хотите узнать погоду. {configure.calendar}\n"
                                      f"Если введете произвольный набор букв, "
                                      f"по-умолчанию произведется выбор погоды на сегодня.\n")
    bot.send_message(message.chat.id, f"Для того, чтобы начать, нажмите /town. {configure.calendar}\n")


@bot.message_handler(commands=['start'])
def cmd_start(message: Message):
    bot.send_sticker(message.chat.id, configure.hello_sticker_id)
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name} {message.from_user.last_name}!\n'
                                      'Я бот, который подскажет тебе прогноз погоды.\n'
                                      f'Чтобы познакомиться со мной нажмите команду /info')



@bot.message_handler(commands=['town'])
def start_weather_bot(message):
    bot.send_message(message.chat.id, f"Укажите наименование города.{configure.house}\n")
    bot.register_next_step_handler(message, get_town)


@bot.message_handler(commands=['another_day'])
def get_another_day(message):
    bot.send_message(message.chat.id, f"Введите другой день.\n")
    bot.register_next_step_handler(message, get_weather_for_day)


@bot.message_handler(content_types=['text'])
def get_town(message):
    global town_from_message
    town_from_message = message.text
    print(message)
    global town_url_dict
    town_url_dict = get_town_name(town_from_message)
    print(town_url_dict)
    if town_url_dict == 'Город не найден':
        bot.send_message(message.chat.id, f"Извини, но я не знаю такого города.")
        bot.send_sticker(message.chat.id, configure.crying_morty)
        bot.send_message(message.chat.id, f"Давай попробуем ввести город еще раз.")
        bot.register_next_step_handler(message, get_town)
    else:
        town_url_upd = list(town_url_dict.keys())
        bot.send_message(message.chat.id, f"Выберите из списка.")
        for i in town_url_upd:
            bot.send_message(message.chat.id, f"{i}")
        bot.register_next_step_handler(message, get_day)


@bot.message_handler(content_types=['text'])
def get_day(message):
    global get_day_url
    global town_name_for_info
    try:
        get_day_url = town_url_dict[message.text]
        town_name_for_info = message.text
    except KeyError:
        get_day_url = town_url_dict[list(town_url_dict.keys())[0]]
        town_name_for_info = list(town_url_dict.keys())[0]
    global day_urls_for_town

    day_urls_for_town = weather_for_week_urls(get_day_url)
    bot.send_message(message.chat.id, 'Выберите день, на который хотите узнать погоду.\n'
                                      'Сегодня\n'
                                      'Завтра\n'
                                      'Через 3 дня\n'
                                      'Через 4 дня\n'
                                      'Через 5 дней\n'
                                      'Через 6 дней\n'
                                      'Через неделю\n')
    bot.register_next_step_handler(message, get_weather_for_day)
    print(day_urls_for_town)


@bot.message_handler(content_types=['text'])
def get_weather_for_day(message):
    global get_day_from_user
    try:
        get_day_from_user = configure.week_day_dict[message.text]
    except KeyError:
        get_day_from_user = configure.week_day_dict[list(configure.week_day_dict.keys())[0]]
    get_weather_data = get_weather_info(get_day_from_user)
    print(get_weather_data)
    weather_data = {'Время': configure.time_weather_list,
                    't': get_weather_data[2],
                    'Ветер, м/с': get_weather_data[4],
                    'emoji': get_weather_data[1]}
    road_data = {'Время': configure.time_weather_list, 'Описание': get_weather_data[-1]}
    info_for_send = tabulate(weather_data, headers=list(weather_data.keys()), tablefmt='github', )
    if len(get_weather_data[-1])>0:
        road_for_send = tabulate(road_data, headers=list(road_data.keys()), tablefmt='github', )
    else:
        road_for_send = 'Извините, информация о состоянии на дорогах недоступна.'
    bot.send_message(message.chat.id, f'{town_name_for_info}\n\n'
                                      f'Прогноз погоды на {get_weather_data[0]}\n\n'
                                      f'{info_for_send}\n'
                                      f'Среднесуточные осадки, мм: {get_weather_data[3]}')
    bot.send_message(message.chat.id, f'Состояние на дорогах.\n'
                                      f' {road_for_send}')
    sleep(3.0)
    bot.send_message(message.chat.id, f'Для того чтобы вбырать другой город, нажмите /town .\n'
                                      f'Для того, чтобы выбрать другой день, нажмите /another_day')


if __name__ == '__main__':
    bot.infinity_polling()

