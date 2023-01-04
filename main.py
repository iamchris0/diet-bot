import telebot
from telebot import types
import sqlite3
import requests
import random
from bs4 import BeautifulSoup as bs
from datetime import date as dt

from app import TOKEN

bot = telebot.TeleBot(TOKEN)

connect = sqlite3.connect('diets.db')
cursor = connect.cursor()

try:
    query = "CREATE TABLE \"diets\" (\
            \"random_id\" INTEGER, \
            \"user_id\" BIGINT, \
            \"Recept\" TEXT, \
            \"Calories\" FLOAT, \
            \"date_n\" DATETIME, \
            PRIMARY KEY(\"random_id\"))"
    cursor.execute(query)
except:
    pass

connect = sqlite3.connect('pref.db')
cursor = connect.cursor()
try:
    query2 = "CREATE TABLE \"pref\" (\
            \"random_id\" INTEGER, \
            \"user_id\" BIGINT, \
            \"recept\" TEXT, \
            \"izbrannoe_status\" BOOLEAN, \
            PRIMARY KEY(\"random_id\"))"
    cursor.execute(query2)
except:
    pass

menu = {}
href = {}
random_choice = [947, 1271, 4633, 4652, 5615, 64, 63, 282, 283, 319, 66, 62, 65]
# random_num = range(10**9)


# напишем, что делать нашему боту при команде старт


@bot.message_handler(commands=['start'])
def send_keyboard(message, text="Рады приветствовать!"):
    menu[message.chat.id] = []
    href[message.chat.id] = {}
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = types.KeyboardButton('Рецепты')
    itembtn2 = types.KeyboardButton('Избранное')
    itembtn3 = types.KeyboardButton('Аналитика')
    itembtn4 = types.KeyboardButton("Калории")
    keyboard.add(itembtn1, itembtn2)
    keyboard.add(itembtn3, itembtn4)
    msg = bot.send_message(message.from_user.id,
                           text=text,
                           reply_markup=keyboard)

    # отправим этот вариант в функцию, которая его обработает
    bot.register_next_step_handler(msg, mainfunction)


def mainfunction(call):
    if call.text == "Рецепты":
        send_keyboard_recepies(call, "Выберите категорию")
    elif call.text == "Избранное":
        send_izbrannoe(call)
    elif call.text == "Аналитика":
        send_keyboard_analytics(call, 'Выберите действие')
    elif call.text == "Калории":
        send_keyboard_callories(call, 'Выберите действие')

def get_plans_string(tasks):
    tasks_str = []
    for val in list(enumerate(tasks)):
        nam = name(val[1][0])
        tasks_str.append(str(val[0] + 1) + ') ' + nam + ' - ' + val[1][0] + '\n')
    return ''.join(tasks_str)

def name(link):
    req = requests.get(link)
    req = bs(req.content, 'html.parser')
    nam = req.find('h1', {'itemprop': 'name'}).text
    return nam

def show_plans(call):
    with sqlite3.connect('pref.db') as con:
        cursor = con.cursor()
        cursor.execute("SELECT recept FROM pref WHERE user_id=={}".format(call.from_user.id))
        tasks = get_plans_string(cursor.fetchall())
        bot.send_message(call.chat.id, tasks)
        con.commit()
        # send_keyboard(call, "Чем еще могу помочь?")

def send_izbrannoe(call):
    keyboard = types.ReplyKeyboardMarkup(row_width=1)
    itembtn19 = types.KeyboardButton('Просмотреть полный список')
    itembtn29 = types.KeyboardButton('Редактировать список')
    itembtn39 = types.KeyboardButton('Очистить избранное')
    itembtn49 = types.KeyboardButton("Вернуться в меню")
    keyboard.add(itembtn19)
    keyboard.add(itembtn29)
    keyboard.add(itembtn39)
    keyboard.add(itembtn49)
    msg = bot.send_message(call.from_user.id,
                           text='Выберите действие',
                           reply_markup=keyboard)
    bot.register_next_step_handler(msg, callback_worker_izbrannoe)


def callback_worker_izbrannoe(call):
    if call.text == 'Просмотреть полный список':
        try:
            show_plans(call)
            send_izbrannoe(call)
        except:
            bot.send_message(call.chat.id, 'Здесь пусто. Добавьте рецепт')
            send_izbrannoe(call)
    elif call.text == 'Редактировать список':
        try:
            delete_one_plan(call)
        except:
            bot.send_message(call.chat.id, 'Здесь пусто. Можно отдыхать :-)')
            send_keyboard(call, "Вы в меню. Рады вас снова видеть :)")
    elif call.text == 'Очистить избранное':
        try:
            delete_all_plans(call)
        except:
            bot.send_message(call.chat.id, 'Здесь пусто. Можно отдыхать :-)')
            send_keyboard(call, "Чем еще могу помочь?")
    else:
        send_keyboard(call, text='Вы в меню. Рады вас снова видеть :)')

def delete_one_plan(msg):
    with sqlite3.connect('pref.db') as con:
        cursor = con.cursor()
        cursor.execute('SELECT recept FROM pref WHERE user_id=={}'.format(msg.from_user.id))
        tasks = cursor.fetchall()
        if len(tasks) == 0:
            bot.send_message(msg.chat.id, 'Здесь пусто. \n Удалять нечего. \n Вернитесь в меню.')
            send_izbrannoe(msg)
            return
        else:
            markup = types.ReplyKeyboardMarkup(row_width=1)
            for value in range(len(tasks)):
                btn = name(tasks[value][0]) + ' - ' + tasks[value][0]
                markup.add(types.KeyboardButton(btn))
            msg = bot.send_message(msg.from_user.id,
                                   text="Выберите одно рецепт из списка",
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, delete_one_plan_)

def delete_one_plan_(msg):
    with sqlite3.connect('pref.db') as con:
        cursor = con.cursor()
        thing = msg.text
        thing = thing.split(' - ')[1]
        cursor.execute('DELETE FROM pref WHERE user_id==? AND recept==?', (msg.from_user.id, thing))
        bot.send_message(msg.chat.id, 'Выбранный рецепт был удален!')
        send_izbrannoe(msg)
        con.commit()

def delete_all_plans(msg):
    with sqlite3.connect('pref.db') as con:
        cursor = con.cursor()
        cursor.execute('DELETE FROM pref WHERE user_id=={}'.format(msg.from_user.id))
        con.commit()
    bot.send_message(msg.chat.id, 'Удалены все рецепты из избранного. Хорошего отдыха!')
    send_izbrannoe(msg)



def send_keyboard_recepies(message, text='что хочите'):
    keyboard = types.ReplyKeyboardMarkup(row_width=1)
    itembtn11 = types.KeyboardButton('Установить фильтр')
    itembtn21 = types.KeyboardButton('Случайное блюдо')
    itembtn15 = types.KeyboardButton('Вернуться назад')
    keyboard.add(itembtn11, itembtn21, itembtn15)
    msg = bot.send_message(message.from_user.id, text=text, reply_markup=keyboard)
    bot.register_next_step_handler(msg, callback_worker_recepies)


def callback_worker_recepies(call):
    if call.text == "Установить фильтр":
        keyboard_menu(call, 'Шаг 1. Выберите меню')
    elif call.text == "Случайное блюдо":
        bot.send_message(call.chat.id, text='Ознакомьтесь пожалуйста')
        menu[call.chat.id] = [random.choice(random_choice)]
        href[call.chat.id] = {'link': b(sorted(menu[call.chat.id])), 'index': 0}
        if len(href[call.chat.id]['link']) == 0:
            bot.send_message(call.chat.id, text='По выбранным данным рецепт не найден')
            menu[call.chat.id] = []
            keyboard_menu(call, text='Выберите заново')
        elif href[call.chat.id]['index'] == len(href[call.chat.id]['link']):
            main_reciept(call)
            bot.send_message(call.chat.id, text='Это был последний рецепт')
            keyboard_found_receipt_last(call, text='Выберите действие')
        else:
            main_reciept(call)
            keyboard_found_receipt(call, text='Выберите действие')
    elif call.text == 'Вернуться назад':
        send_keyboard(call, text='Вы в меню. Рады вас снова видеть :)')


def keyboard_menu(message, text='so'):
    keyboard = types.ReplyKeyboardMarkup(row_width=3)
    itembtn = types.KeyboardButton('Перейти к выбору ингредиентов')
    itembtn1 = types.KeyboardButton('Завтрак')
    itembtn2 = types.KeyboardButton('Обед')
    itembtn3 = types.KeyboardButton('Перекус')
    itembtn4 = types.KeyboardButton('Ужин')
    itembtn5 = types.KeyboardButton('Правильное питание')
    itembtn6 = types.KeyboardButton('Диетическое')
    itembtn7 = types.KeyboardButton('Вегетарианское')
    itembtn8 = types.KeyboardButton('Низкокалорийное')
    itembtn9 = types.KeyboardButton('Пикник')
    itembtn10 = types.KeyboardButton('Повседневное')
    itembtn11 = types.KeyboardButton('Постное')
    itembtn12 = types.KeyboardButton('Праздничное')
    itembtn13 = types.KeyboardButton('Вернуться назад')
    itembtnback = types.KeyboardButton('Вернуться в меню')
    keyboard.add(itembtn)
    keyboard.add(itembtn1, itembtn2, itembtn3)
    keyboard.add(itembtn4, itembtn5, itembtn6)
    keyboard.add(itembtn7, itembtn8, itembtn9)
    keyboard.add(itembtn10, itembtn11, itembtn12)
    keyboard.add(itembtn13)
    keyboard.add(itembtnback)

    msg = bot.send_message(message.from_user.id, text=text, reply_markup=keyboard)
    # отправим этот вариант в функцию, которая его обработает
    bot.register_next_step_handler(msg, callback_worker_menu)


def callback_worker_menu(call):
    if call.text == 'Перейти к выбору ингредиентов':
        keyboard_ingredients(call, text='Шаг 2. Выберите ингредиенты')
    elif call.text == 'Вернуться назад':
        menu[call.chat.id] = []
        send_keyboard_recepies(call, text='Выберите категорию')
    elif call.text == 'Вернуться в меню':
        send_keyboard(call, text='Вы в меню. Рады вас снова видеть :)')
    else:
        menu[call.chat.id].append(filter_worker_menu(call))
        keyboard_menu(call, text='Добавить что-то еще?')


def filter_worker_menu(call):
    filters = 0
    if call.text == 'Завтрак':
        filters = 947
    if call.text == 'Обед':
        filters = 1271
    if call.text == 'Перекус':
        filters = 4633
    if call.text == 'Ужин':
        filters = 4652
    if call.text == 'Правильное питание':
        filters = 5615
    if call.text == 'Детское':
        filters = 64
    if call.text == 'Диетическое':
        filters = 63
    if call.text == 'Вегетарианское':
        filters = 282
    if call.text == 'Низкокалорийное':
        filters = 283
    if call.text == 'Пикник':
        filters = 319
    if call.text == 'Повседневное':
        filters = 66
    if call.text == 'Постное':
        filters = 62
    if call.text == 'Праздничное':
        filters = 65
    return filters


def keyboard_ingredients(message, text='Выберите ингридиенты'):
    keyboard = types.ReplyKeyboardMarkup(row_width=3)
    itembtn = types.KeyboardButton('Показать рецепты')
    itembtn1 = types.KeyboardButton('Мясное')
    itembtn2 = types.KeyboardButton('Птица')
    itembtn3 = types.KeyboardButton('Рыба')
    itembtn4 = types.KeyboardButton('Морепродукты')
    itembtn5 = types.KeyboardButton('Овощи')
    itembtn6 = types.KeyboardButton('Яйца')
    itembtn7 = types.KeyboardButton('Мучное')
    itembtn8 = types.KeyboardButton('Макаронные изделия')
    itembtn9 = types.KeyboardButton('Молочные продукты')
    itembtn10 = types.KeyboardButton('Сыр')
    itembtn11 = types.KeyboardButton('Крупы')
    itembtn12 = types.KeyboardButton('Грибы')
    itembtn13 = types.KeyboardButton('Фрукты')
    itembtn14 = types.KeyboardButton('Зелень')
    itembtn15 = types.KeyboardButton('Специи и пряности')
    itembtn16 = types.KeyboardButton('Ягоды')
    itembtn17 = types.KeyboardButton('Орехи')
    itembtn18 = types.KeyboardButton('Сухофрукты')
    itembtn19 = types.KeyboardButton('Масла и жиры')
    itembtn20 = types.KeyboardButton('Консервация')
    itembtn21 = types.KeyboardButton('Соусы')
    itembtn22 = types.KeyboardButton('Вернуться назад')
    itembtnback = types.KeyboardButton('Вернуться в меню')
    keyboard.add(itembtn)
    keyboard.add(itembtn1, itembtn2, itembtn3)
    keyboard.add(itembtn4, itembtn5, itembtn6)
    keyboard.add(itembtn7, itembtn8, itembtn9)
    keyboard.add(itembtn10, itembtn11, itembtn12)
    keyboard.add(itembtn13, itembtn14, itembtn15)
    keyboard.add(itembtn16, itembtn17, itembtn18)
    keyboard.add(itembtn19, itembtn20, itembtn21)
    keyboard.add(itembtn22)
    keyboard.add(itembtnback)
    msg = bot.send_message(message.from_user.id, text=text, reply_markup=keyboard)
    bot.register_next_step_handler(msg, callback_worker_ingredients)


def callback_worker_ingredients(call):
    if call.text == 'Показать рецепты':
        bot.send_message(call.chat.id, text='Ваш рецепт')
        href[call.chat.id] = {'link': b(sorted(menu[call.chat.id])), 'index': 0}
        if len(href[call.chat.id]['link']) == 0:
            bot.send_message(call.chat.id, text='По выбранным данным рецепт не найден')
            menu[call.chat.id] = []
            keyboard_menu(call, text='Выберите заново')
        elif (href[call.chat.id]['index'] + 1) == len(href[call.chat.id]['link']):
            main_reciept(call)
            bot.send_message(call.chat.id, text='Это был последний рецепт')
            keyboard_found_receipt_last(call, text='Выберите действие')
        else:
            main_reciept(call)
            keyboard_found_receipt(call, text='Выберите действие')
    elif call.text == 'Вернуться назад':
        keyboard_menu(call, text='ок')
    elif call.text == 'Вернуться в меню':
        send_keyboard(call, text='Вы в меню. Рады вас снова видеть :)')
    else:
        # функция с кусками ссылок для каждого ингредиента
        menu[call.chat.id].append(filter_worker_ingredients(call))
        keyboard_ingredients(call, text='Что еще?')

def main_reciept(call):
    link = 'https://tvoirecepty.ru/' + str(href[call.chat.id]['link'][href[call.chat.id]['index']])
    info = about_recipe(link)
    name = info[0]
    review = info[1]
    rating = info[2]
    cooking_time = info[3]
    method = info[4]
    calorie = info[5]
    protein = info[6]
    fat = info[7]
    carbohydrates = info[8]
    dic = info[9]
    recip = ''
    for i in dic:
        recip += i + ': ' + dic[i] + '\n'
    amount = info[10]
    picture = info[11]
    bot.send_photo(call.chat.id, picture)
    text = f"*{name}*" + '\n' + '\n' + review + '\n' + rating + '\n' + str(cooking_time) + \
           '\n' + str(method) + '\n' + '\n' + str(calorie) + '\n' + str(protein) + '\n' + str(fat) + '\n' + \
            str(carbohydrates) + '\n' + '\n' + str(amount) + '\n' + '\n' + "_Ингредиенты: _" + '\n' + recip + \
            '\n' + 'Инструкция по приготовлению:' + '\n' + link
    bot.send_message(call.chat.id, text=text, parse_mode="Markdown")
    href[call.chat.id]['index'] += 1


def filter_worker_ingredients(call):
    filters = 0
    if call.text == 'Мясное':
        filters = 1
    if call.text == 'Птица':
        filters = 4018
    if call.text == 'Рыба':
        filters = 74
    if call.text == 'Морепродукты':
        filters = 85
    if call.text == 'Овощи':
        filters = 3
    if call.text == 'Яйца':
        filters = 86
    if call.text == 'Мучное':
        filters = 76
    if call.text == 'Макаронные изделия':
        filters = 4022
    if call.text == 'Молочные продукты':
        filters = 75
    if call.text == 'Сыр':
        filters = 4021
    if call.text == 'Крупы':
        filters = 79
    if call.text == 'Грибы':
        filters = 4019
    if call.text == 'Фрукты':
        filters = 73
    if call.text == 'Зелень':
        filters = 72
    if call.text == 'Масла и жиры':
        filters = 71
    if call.text == 'Ягоды':
        filters = 87
    if call.text == 'Орехи':
        filters = 4020
    if call.text == 'Сухофрукты':
        filters = 4023
    if call.text == 'Специи и пряности':
        filters = 390
    if call.text == 'Консервация':
        filters = 88
    if call.text == 'Соусы':
        filters = 77
    if call.text == 'Алкоголь':
        filters = 434
    return filters


def b(filters):
    # array of filters
    mas = []
    filters_string = ["tid:{}".format(x) for x in filters]
    f_s = " AND ".join(filters_string)

    headers = {
        'authority': 'tvoirecepty.ru',
        'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'x-requested-with': 'XMLHttpRequest',
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://tvoirecepty.ru',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://tvoirecepty.ru/recepty',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'cookie': 'has_js=1; currency=RUB; analytics_uid=F9C04766-BF9A-4969-A1E3-089FF0544016; analytics_first_source=direct; _ym_uid=1623924323813931656; _ym_d=1623924323; _ga=GA1.2.F9C04766-BF9A-4969-A1E3-089FF0544016; _gid=GA1.2.1161744416.1623924323; _ym_isad=1; _ym_visorc=w; analytics_days_from_last_visit=186; analytics_last_visit=1623924993514; analytics_visit_number=2; analytics_session_pageviews=2; _dc_gtm_UA-16302740-2=1; _gat_UA-16302740-2=1; _gali=parent-8',
    }

    data = {
        'deftype': 'dismax',
        'fl': 'title,type,nid,ss_field_image,created,sm_field_recept_ingredient,is_field_recept_calories_per_100,ps_field_recept_portions,is_rate_down,is_rate_up,is_field_recept_cooktime,path_alias,is_flag_count,ps_field_recept_carbohydr_per_100,ps_field_recept_fats_per_100,ps_field_recept_protein_per_100,ps_field_price,comment_count',
        'mm': '1',
        'wt': 'json',
        'rows': '20',
        'start': '0',
        'facet': 'on',
        'sort': 'score desc',
        'facet.field': 'tid',
        'fq': 'type:recept AND (' + f_s + ') AND is_field_recept_calories_per_100:[0 TO 800] AND is_field_recept_cooktime:[0 TO 240] AND is_prop_recept_fats:[0 TO 100] AND is_prop_recept_carbohydr:[0 TO 100] AND is_prop_recept_protein:[0 TO 100] AND ps_field_price:[0 TO 16] AND (status:1)',
        'qf': 'title^1',
        'facet.limit': '1000'
    }

    response = requests.post('https://tvoirecepty.ru/solr/tvoirecepty.ru/select', headers=headers, data=data)

    for i in range(len(response.json()['response']['docs'])):
        mas.append(response.json()['response']['docs'][i]['path_alias'])

    return mas


def about_recipe(link):
    req = requests.get(link)
    req = bs(req.content, 'html.parser')
    name = []
    values = []
    dic = {}

    # Название
    nam = req.find('h1', {'itemprop': 'name'}).text

    # Оценка
    try:
        rate = req.find('span', {'class': 'review vcenter hidden-xs'}).em.text.replace('\n', '').strip()[1:-1]
        rate = rate.strip()
        qwer = rate.split()
        reviews = ''
        rating = ''
        second = ' ' + qwer[1][:-1]
        qwer[2] = qwer[2].title()
        text1 = [qwer[0], second]
        text2 = qwer[2:]
        for i in text1:
            reviews += i
        for j in text2:
            rating += j + ' '
        rating = rating.strip()
    except:
        reviews = 'Оценка отсутствует'
        rating = 'Рейтинг отсутствует'

    # Инфа о калориях и тд
    try:
        cooking_time = req.find('div', {'class': 'pull-left row'}).text.strip() + ' ' + req.find('span', {
            'class': 'bor font-130'}).text
    except:
        cooking_time = 'Время приготовления отсутствует'

    # метод приготовления
    try:
        method = req.find('div', {'class': 'col-xs-12 margin-bottom-15'}).find('div', {
            'class': 'pull-left row'}).text.strip() + ' ' + req.find('div',
                                                                     {'class': 'col-xs-12 margin-bottom-15'}).find(
            'span', {'class': 'tags-link tag-link jslink'}).text.strip()
    except:
        method = 'Информация о методе приготовления отсутствует'

    # ЖБУ
    try:
        calorie = req.find('div', {'class': 'col-xs-12 margin-bottom-10'}).find('div', {
            'class': 'pull-left row'}).text.strip() + ' ' + req.find('p', {
            'class': 'doughnutSummaryNumber'}).text + ' ' + req.find('p', {
            'class': 'doughnutSummaryTitle type'}).text + ' ' + req.find('div',
                                                                         {'class': 'col-xs-12 margin-bottom-10'}).find(
            'div', {'class': 'pull-right font-130 row-xs calories'}).text.strip()
        pfc = req.find_all('div', {'class': 'pull-left margin-bottom-5'})
        protein = pfc[0].text + ':' + ' ' + req.find('div', {'class': 'pull-right row-xs protein'}).text
        fat = pfc[1].text + ':' + ' ' + req.find('div', {'class': 'pull-right row-xs fat'}).text
        carbohydrates = pfc[2].text + ':' + ' ' + req.find('div', {'class': 'pull-right row-xs carbohydrates'}).text
    except:
        protein = 0
        fat = 0
        carbohydrates = 0

    # Находим инфу об ингредиентах
    try:
        for item in req.find_all('div', {'class': 'name pull-left'}):
            try:
                name.append(item.span.text)
            except:
                name.append(item.text.strip())
        for jtem in req.find_all('div', {'class': "pull-right"}):
            values.append(jtem.text.replace('\n', ' ').strip())
        values = values[len(values) - len(name) - 2:-2]
        for i in range(len(values)):
            dic[name[i]] = values[i]
    except:
        dic = 'Информации о количестве ингредиентов не найдено'

    try:
        amount = 'Количество порций: ' + req.find('span', {'class': 'yield-wrapper'}).get('rel')
    except:
        amount = 'Количество порций не определено'

    # Рецепт
    try:
        recipe = [0] * len(req.find_all('div', {'class': 'instruction row-xs margin-bottom-20'}))
        for q in range(len(req.find_all('div', {'class': 'instruction row-xs margin-bottom-20'}))):
            sag = req.find_all('div', {'class': 'instruction row-xs margin-bottom-20'})[q].text[5:].strip()
            recipe[q] = sag
        recipe[len(recipe) - 1] = 'Рецепт готов!'
    except:
        recipe = 'Ссылка на рецепт'

    # Картинка блюда
    try:
        picture = str(req.find_all('div', {'class': 'col-xs-12 col-md-12 pull-left nopadding recipe-image-bg'})[0])
        picture = picture[(picture.find('url') + 4):picture.find(')')]
    except:
        picture = 'https://im0-tub-ru.yandex.net/i?id=a5c89ef96353146d6a9c1ad43dc16076-l&n=13'

    return [nam, reviews, rating, cooking_time, method, calorie, protein, fat, carbohydrates, dic, amount, picture]


def callback_worker_found_receipt(call):
    if call.text == 'Добавить в избранное':
        callback_izbrannoe(call)
        keyboard_found_receipt(call, text='Выберите действие')
    if call.text == 'Очистить фильтры':
        href[call.chat.id] = {}
        menu[call.chat.id] = []
        bot.send_message(call.chat.id, text='Фильтры очищены')
        send_keyboard_recepies(call, text='Выберите действие')
    if call.text == 'Добавить калории':
        choice(call)
    if call.text == 'Следующий рецепт':
        main_reciept(call)
        # если у нас ЭТО последняя ссылка - вызываем клавиатуру БЕЗ кнопки "следующий рецепт"
        if href[call.chat.id]['index'] == len(href[call.chat.id]['link']):
            bot.send_message(call.chat.id, text='Это был последний рецепт')
            keyboard_found_receipt_last(call, text='Выберите действие')
        else:
            keyboard_found_receipt(call, text='Выберите действие')
    if call.text == 'Вернуться назад':
        keyboard_menu(call, text='Выберите повторно меню')
    if call.text == 'Вернуться в меню':
        send_keyboard(call, text='Вы в меню. Рады вас снова видеть :)')


def choice(call):
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    itembtn01 = types.KeyboardButton('Да')
    itembtn02 = types.KeyboardButton('Нет')
    keyboard.add(itembtn01, itembtn02)
    msg = bot.send_message(call.from_user.id, text='Собираетесь ли вы готовить данное блюдо?', reply_markup=keyboard)
    bot.register_next_step_handler(msg, callback_worker_choice)

def callback_worker_choice(call):
    if call.text == 'Да':
        with sqlite3.connect('diets.db') as con:
            cursor = con.cursor()
            random_id = random.randint(0, 10 ** 15)
            user_id = call.from_user.id
            recept = 'https://tvoirecepty.ru/' + str(href[call.chat.id]['link'][href[call.chat.id]['index'] - 1])
            req = requests.get(recept)
            req = bs(req.content, 'html.parser')
            calorie = float(req.find('p', {'class': 'doughnutSummaryNumber'}).text) * 3.5
            date = str(dt.today())
            cursor.execute(
                "INSERT OR IGNORE INTO diets(random_id, user_id, Recept, Calories, date_n) VALUES (?, ?, ?, ?, ?)",
                (random_id, user_id, recept, calorie, date))
            bot.send_message(call.from_user.id, 'Калории успешно добавлены')
            con.commit()
        if href[call.chat.id]['index'] == len(href[call.chat.id]['link']):
            keyboard_found_receipt_last(call, text='Выберите действие')
        else:
            keyboard_found_receipt(call)
    elif call.text == 'Нет':
        bot.send_message(call.chat.id, text='Вы какой-то странный, оно же такое вкусное...')
        if href[call.chat.id]['index'] == len(href[call.chat.id]['link']):
            keyboard_found_receipt_last(call, text='Выберите действие')
        else:
            keyboard_found_receipt(call)



def callback_izbrannoe(call):
    with sqlite3.connect('pref.db') as con:
        cursor = con.cursor()
        random_id = random.randint(0, 10**15)
        user_id = call.from_user.id
        recept = 'https://tvoirecepty.ru/' + str(href[call.chat.id]['link'][href[call.chat.id]['index']])
        flag = True
        cursor.execute("INSERT OR IGNORE INTO pref(random_id, user_id, recept, izbrannoe_status) VALUES (?, ?, ?, ?)",
                       (random_id, user_id, recept, flag))
        bot.send_message(call.from_user.id, 'Рецепт успешно сохранен')
        con.commit()


def send_keyboard_callories(message, text='Выберите действие'):
    keyboard = types.ReplyKeyboardMarkup(row_width=1)
    itembtn11 = types.KeyboardButton('Калории за сегодня')
    itembtn21 = types.KeyboardButton('Рассчитать калории')
    itembtn4 = types.KeyboardButton('Вернуться назад')
    keyboard.add(itembtn11, itembtn21)
    keyboard.add(itembtn4)
    msg = bot.send_message(message.from_user.id, text=text, reply_markup=keyboard)
    bot.register_next_step_handler(msg, callback_worker_callories)


def callback_worker_callories(call):
    if call.text == "Калории за сегодня":
        try:
            show_calories(call)
            send_keyboard_callories(call)
        except:
             bot.send_message(call.chat.id, 'Сегодня вы ничего не съели')
             send_keyboard(call, "Выберите действие")
    if call.text == "Рассчитать калории":
        age = bot.send_message(call.chat.id, 'Введите свой возраст с клавиатуры!')
        bot.register_next_step_handler(age, a)
    if call.text == 'Вернуться назад':
        send_keyboard(call, text="Вы в меню. Рады вас снова видеть :)")

def get_calories_today(tasks):
    sum = 0
    for val in list(enumerate(tasks)):
        sum += float(val[1][0])
        # tasks_str.append(str(val[1][0]))
    return sum

def show_calories(msg):
    with sqlite3.connect('diets.db') as con:
        cursor = con.cursor()
        date = str(dt.today())
        cursor.execute('SELECT Calories FROM diets WHERE user_id==? AND date_n==?', (msg.from_user.id, date))
        tasks = 'За сегодня вам удалось съесть' + '\n' + str(get_calories_today(cursor.fetchall())) + ' калорий.'
        bot.send_message(msg.chat.id, text=tasks)
        #send_keyboard(msg, "Чем еще могу помочь?")
        con.commit()



def a(m):
    global ages
    ages = m.text
    keyboard_sex(m)

def keyboard_sex(m, text='Выберите свой пол'):
    keyboard = types.ReplyKeyboardMarkup(row_width=2)  # наша клавиатура
    itembtn1 = types.KeyboardButton('Мужской')  # создадим кнопку
    itembtn3 = types.KeyboardButton('Женский')
    keyboard.add(itembtn1, itembtn3)
    msg = bot.send_message(m.from_user.id, text=text, reply_markup=keyboard)
    bot.register_next_step_handler(msg, callback_worker_sex)

def callback_worker_sex(call):
    global sexs
    sexs = call.text
    weight = bot.send_message(call.chat.id, text='Укажите свой вес (введите с клавиатуры!)')
    bot.register_next_step_handler(weight, aaa)

def aaa(m):
    global weights
    weights = m.text
    tall = bot.send_message(m.chat.id, text='Укажите свой рост (введите с клавиатуры!)')
    bot.register_next_step_handler(tall, aaaa)

def aaaa(m):
    global talls
    talls = m.text
    new_keyboard(m, 'Укажите уровень своей активности')


def new_keyboard(message, text='Выберите пожалуйста'):
    keyboard = types.ReplyKeyboardMarkup(row_width=2)  # наша клавиатура
    itembtn1 = types.KeyboardButton('Минимум/отсутствие активности')  # создадим кнопку
    itembtn3 = types.KeyboardButton('3 раза в неделю')
    itembtn4 = types.KeyboardButton('5 раз в неделю')  # создадим кнопку
    itembtn5 = types.KeyboardButton('5 раз в неделю интенсивно')
    itembtn6 = types.KeyboardButton('Каждый день')
    itembtn7 = types.KeyboardButton('Каждый день интесивно')
    itembtn8 = types.KeyboardButton('Ежедневная работа')

    keyboard.add(itembtn1, itembtn3, itembtn4, itembtn5, itembtn6, itembtn7, itembtn8)
    msg = bot.send_message(message.from_user.id, text=text, reply_markup=keyboard)
    bot.register_next_step_handler(msg, callback_worker_activity)


def callback_worker_activity(call):
    global activity
    activity = call.text
    result = round(formula(ages,weights,sexs,talls,activity), 3)
    bot.send_message(call.chat.id,'Ваша норма калорий в день:')
    bot.send_message(call.chat.id,result)
    send_keyboard_callories(call)

def formula(ages,weights,sexs,talls,activity):
    k = 0
    if activity == 'Минимум/отсутствие активности':
        k = 1.2
    if activity == '3 раза в неделю':
        k = 1.38
    if activity == '5 раз в неделю':
        k = 1.46
    if activity == '5 раз в неделю интенсивно':
        k = 1.55
    if activity == 'Каждый день':
        k = 1.64
    if activity == 'Каждый день интесивно':
        k = 1.73
    if activity == 'Ежедневная работа':
        k = 1.9
    w = int(weights)
    a = int(ages)
    t = int(talls)
    if sexs == 'Мужской':
        r = (10 * w + t * 6.25 + a * 5 + 5) * k
    else:
        r = (10 * w + t * 6.25 + a * 5 - 161) * k
    return r


def send_keyboard_analytics(message, text='что хочите'):
    keyboard = types.ReplyKeyboardMarkup(row_width=1)
    itembtn21 = types.KeyboardButton('За сегодня')
    itembtn15 = types.KeyboardButton('Вернуться назад')
    keyboard.add(itembtn21, itembtn15)
    msg = bot.send_message(message.from_user.id, text=text, reply_markup=keyboard)

    # отправим этот вариант в функцию, которая его обработает
    bot.register_next_step_handler(msg, callback_worker_analytics)


def callback_worker_analytics(call):
    if call.text == "За сегодня":
        try:
            with sqlite3.connect('diets.db') as con:
                cursor = con.cursor()
                date = str(dt.today())
                cursor.execute('SELECT Recept FROM diets WHERE user_id==? AND date_n==?', (call.from_user.id, date))
                pfc = bju(cursor.fetchall())
                dolya = []
                for i in range(len(pfc) - 1):
                    dolya.append(pfc[i] / pfc[-1])
                pfc = pfc[:3]
                text = "Белки" + ": " + str(round(pfc[0])) + ". Доля во всем объеме - " + str(round(dolya[0], 2) * 100) + '%' + '\n' + \
                       "Жиры" + ": " + str(round(pfc[1])) + ". Доля во всем объеме - " + str(round(dolya[1], 2) * 100)  + '%' + '\n' + \
                       "Углеводы" + ": " + str(round(pfc[2])) + ". Доля во всем объеме - " + str(round(dolya[2], 2) * 100) + '%'
                bot.send_message(call.chat.id, text=text)
                con.commit()
            # fig = plt.pie(pfc)
            # labels = ['Белки', 'Жиры', 'Углеводы']
            # photo = plt.pie(fig, labels=labels, autopct='%1.1f%%')
            # photo.savefig('saved_figure.pdf')
            # bot.send_photo(call.chat.id, open('saved_figure.pdf', 'rb'))
            # bot.send_message(call.from_user.id, 'Калории успешно добавлены')
        except:
            bot.send_message(call.chat.id, text='Анализировать нечего, идите кушать.')
        send_keyboard(call, text='Вы в меню, рады вас видеть :)')
    elif call.text == 'Вернуться назад':
        send_keyboard(call, text='Вы в меню, рады вас видеть :)')

def bju(call):
    protein2 = 0
    fat2 = 0
    carbohydrates2 = 0
    for item in call:
        link = item[0]
        req = requests.get(link)
        req = bs(req.content, 'html.parser')
        protein = req.find('div', {'class': 'pull-right row-xs protein'}).text
        protein2 += float(protein.split()[0])
        fat = req.find('div', {'class': 'pull-right row-xs fat'}).text
        fat2 += float(fat.split()[0])
        carbohydrates = req.find('div', {'class': 'pull-right row-xs carbohydrates'}).text
        carbohydrates2 += float(carbohydrates.split()[0])
        sum = protein2 + fat2 + carbohydrates2
    return [protein2, fat2, carbohydrates2, sum]




def send_keyboard_chosen(message, text='что хочите'):
    keyboard = types.ReplyKeyboardMarkup(row_width=1)
    itembtn11 = types.KeyboardButton('Посмотреть')
    itembtn21 = types.KeyboardButton('Редактировать')
    itembtn15 = types.KeyboardButton('Вернуться назад')
    keyboard.add(itembtn11, itembtn21, itembtn15)
    msg = bot.send_message(message.from_user.id, text=text, reply_markup=keyboard)
    # отправим этот вариант в функцию, которая его обработает
    bot.register_next_step_handler(msg, callback_worker_chosen)


def callback_worker_chosen(call):
    if call.text == "Посмотреть":
        msg = bot.send_message(call.chat.id, text='неа')
        send_keyboard_chosen(call, 'Выберите действие')
    elif call.text == "Редактировать":
        msg = bot.send_message(call.chat.id, text='нетт')
        send_keyboard_chosen(call, 'Выберите действие')
    elif call.text == 'Вернуться назад':
        send_keyboard(call, text='Выберите действие')


def keyboard_found_receipt(message, text='Выберите действие'):
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    itembtn = types.KeyboardButton('Добавить в избранное')
    itembtn1 = types.KeyboardButton('Очистить фильтры')
    itembtn2 = types.KeyboardButton('Добавить калории')
    itembtn3 = types.KeyboardButton('Следующий рецепт')
    itembtn4 = types.KeyboardButton('Вернуться назад')
    itembtn5 = types.KeyboardButton('Вернуться в меню')
    keyboard.add(itembtn, itembtn1)
    keyboard.add(itembtn2, itembtn3)
    keyboard.add(itembtn4)
    keyboard.add(itembtn5)
    msg = bot.send_message(message.from_user.id, text=text, reply_markup=keyboard)
    bot.register_next_step_handler(msg, callback_worker_found_receipt)

def keyboard_found_receipt_last(message, text='Выберите действие'):
    keyboard = types.ReplyKeyboardMarkup(row_width=1)
    itembtn = types.KeyboardButton('Добавить в избранное')
    itembtn1 = types.KeyboardButton('Очистить фильтры')
    itembtn2 = types.KeyboardButton('Добавить калории')
    itembtn3 = types.KeyboardButton('Вернуться назад')
    itembtn4 = types.KeyboardButton('Вернуться в меню')
    keyboard.add(itembtn)
    keyboard.add(itembtn1)
    keyboard.add(itembtn2)
    keyboard.add(itembtn3)
    keyboard.add(itembtn4)
    msg = bot.send_message(message.from_user.id, text=text, reply_markup=keyboard)
    bot.register_next_step_handler(msg, callback_worker_found_receipt)


bot.polling(none_stop=True)
