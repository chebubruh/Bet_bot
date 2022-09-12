from telebot import *
from bs4 import BeautifulSoup
from requests import *
from random import choice
from sqlite3 import *
import config

bot = TeleBot(config.TOKEN)


def parse_matches():
    url = 'https://game-tournaments.com/dota-2/matches?tid=3659'

    r = get(url, headers=config.HEADERS)

    soup = BeautifulSoup(r.text, 'lxml')
    data = soup.find('div', id='block_matches_current')
    team1 = data.findAll('span', class_='teamname c1')
    team2 = data.findAll('span', class_='teamname c2')
    # date = data.findAll('span', class_='sct')

    res_team1 = list()
    # res_date = list()

    for i in team1:
        i = i.text.replace('\n', '')
        res_team1.append(i)

    for i in team2:
        i = i.text.replace('\n', '')
        res_team1.append(i)

    # for i in date:
    #     i = i.text.replace('\n', '')
    #     res_date.append(i)

    a = 0

    res_blyat = list()
    res_blyat2 = list()

    for i in range(len(res_team1) // 2):
        res_blyat.append(f'{res_team1[a]} vs {res_team1[a + (len(res_team1) // 2)]}')
        a += 1

    for i in res_blyat:
        if 'TBD' in i:
            continue
        else:
            res_blyat2.append(i)

    return res_blyat2


def parse_matches_res():
    url = 'https://game-tournaments.com/dota-2/matches?tid=3659'

    r = get(url, headers=config.HEADERS)

    soup = BeautifulSoup(r.text, 'lxml')
    data = soup.find('div', id='block_matches_past')
    data_res = data.findAll('span', class_='mbutton')
    res_score = list()
    for i in data_res:
        i = i.get('data-score')
        if i[0] < i[4]:
            res_score.append('P2')
        elif i[0] > i[4]:
            res_score.append('P1')
        else:
            res_score.append('X')
    return res_score


def parse_matches_past():
    url = 'https://game-tournaments.com/dota-2/matches?tid=3659'

    r = get(url, headers=config.HEADERS)

    soup = BeautifulSoup(r.text, 'lxml')
    data = soup.find('div', id='block_matches_past')
    team1 = data.findAll('span', class_='teamname c1')
    team2 = data.findAll('span', class_='teamname c2')
    # date = data.findAll('span', class_='sct')

    res_team1 = list()
    # res_date = list()

    for i in team1:
        i = i.text.replace('\n', '')
        res_team1.append(i)

    for i in team2:
        i = i.text.replace('\n', '')
        res_team1.append(i)

    # for i in date:
    #     i = i.text.replace('\n', '')
    #     res_date.append(i)

    a = 0

    res_blyat = list()
    res_blyat2 = list()

    for i in range(len(res_team1) // 2):
        res_blyat.append(f'{res_team1[a]} vs {res_team1[a + (len(res_team1) // 2)]}')
        a += 1

    for i in res_blyat:
        if 'TBD' in i:
            continue
        else:
            res_blyat2.append(i)

    return res_blyat2


def update():
    with connect('aboba.db') as db:
        cur = db.cursor()
        match = cur.execute("SELECT matches FROM users")
        a = list()
        for i in match:
            for j in i:
                a.append(j)

        for i in parse_matches_past():
            if i in a:
                index = parse_matches_past().index(i)
                cur.execute(f"UPDATE users SET 'result' = '{parse_matches_res()[index]}' WHERE matches == '{i}'")


@bot.message_handler(commands=['start'])
def start(message):
    general_keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    matches = types.KeyboardButton(text='Показать матчи')
    help = types.KeyboardButton(text='🆘 Подсказка 🆘')
    table = types.KeyboardButton(text='📈 Таблица булдыг')
    general_keyboard.add(help, table, matches)
    bot.send_message(message.chat.id, 'Здравствуте, я бот, созданный по лучшему в мире ТЗ!',
                     reply_markup=general_keyboard)
    with connect('aboba.db') as db:
        cur = db.cursor()
        a = cur.execute('pragma table_info(users)')
        name_list = list()
        for i in a:
            name_list.append(i[1])
        if message.from_user.first_name not in name_list:
            cur.execute(f"ALTER TABLE users ADD COLUMN'{message.from_user.first_name}' 'TEXT'")
            cur.execute(f"INSERT INTO points (name) VALUES ('{message.from_user.first_name}')")


@bot.message_handler(func=lambda x: x.text == '📈 Таблица булдыг')
def points(message):
    with connect('aboba.db') as db:
        cur = db.cursor()
        user = message.from_user.first_name

        points = cur.execute(f"SELECT score FROM points WHERE name == '{user}'")
        for i in points:
            for j in i:
                points = j

        a = cur.execute(f"SELECT matches, result, {user} FROM users")
        a = a.fetchall()
        for i in a:
            if i[1] == 'P2' or i[1] == 'P1' or i[1] == 'X':
                if i[1] == i[2]:
                    points += 1
                    cur.execute(f"UPDATE users SET '{user}' = '{i[2]}*' WHERE matches == '{i[0]}'")

        cur.execute(f"UPDATE points SET 'score' = '{points}' WHERE name == '{user}'")

    with connect('aboba.db') as db:
        cur = db.cursor()

        res = list()
        num = 1
        name_str = ''

        a = cur.execute("SELECT name, score FROM points ORDER BY score DESC")
        for i in a:
            res.append(f'{num}. {i[0]} ({i[1]} баллов)')
            num += 1

        for i in res:
            name_str += f'{i}\n'
        bot.send_message(message.chat.id, name_str)


@bot.message_handler(func=lambda x: x.text == '🆘 Подсказка 🆘')
def help(message):
    bot.send_message(message.chat.id,
                     'Если ты не знаешь на кого ставить и тебе необходима помощь специально обученной нейросети, то просто напиши список команд через запятую и я подскажу тебе!\n(Пример записи: Team Spirit, Fnatic)')
    bot.register_next_step_handler(message, help_answer)


def help_answer(message):
    general_keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    matches = types.KeyboardButton(text='Показать матчи')
    help = types.KeyboardButton(text='🆘 Подсказка 🆘')
    table = types.KeyboardButton(text='📈 Таблица булдыг')
    general_keyboard.add(help, table, matches)
    list_answer = message.text.split(',')
    answer = choice(list_answer)
    bot.send_message(message.chat.id, f'Я бы на твоем месте поставил на <b>{answer}</b>', parse_mode='HTML',
                     reply_markup=general_keyboard)


@bot.message_handler(func=lambda x: x.text == 'Показать матчи')
def view_matches(message):
    try:
        with connect('aboba.db') as db:
            cur = db.cursor()
            a = cur.execute('SELECT matches FROM users')
            a = a.fetchall()
            db = list()

            for i in a:
                for j in i:
                    db.append(j)

            for i in parse_matches():
                if i not in db:
                    cur.execute(f"INSERT INTO users (matches) VALUES ('{i}')")
        update()
    except IndexError:
        update()

    with connect('aboba.db') as db:
        cur = db.cursor()
        flag = False
        user = message.from_user.first_name

        z = cur.execute(f'SELECT matches, {user} FROM users')
        for i in z:
            if i[1] != None:
                flag = True
            elif i[1] == None:
                choice_keyboard = types.InlineKeyboardMarkup(row_width=3)
                left = types.InlineKeyboardButton(text='П1',
                                                  callback_data='p1')
                right = types.InlineKeyboardButton(text='П2',
                                                   callback_data='p2')
                drow = types.InlineKeyboardButton(text='X',
                                                  callback_data='x')
                choice_keyboard.add(left, drow, right)
                bot.send_message(message.chat.id, i, reply_markup=choice_keyboard)
                flag = False

    if flag:
        bot.send_message(message.chat.id, 'Ставки сделаны!\nСтавок больше нет!')


@bot.callback_query_handler(func=lambda callback: callback.data)
def callback_check(callback):
    split_teams = callback.message.text.split()
    if callback.data == 'p1':
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f'В матче: {split_teams[0]} vs {split_teams[2]}\n<b>Ты поставил на победу {split_teams[0]}</b>',
                              parse_mode='HTML')

        with connect('aboba.db') as db:
            cur = db.cursor()
            cur.execute(
                f"UPDATE users SET '{callback.from_user.first_name}' = 'P1' WHERE matches == '{callback.message.text}'")

    elif callback.data == 'p2':
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f'В матче: {split_teams[0]} vs {split_teams[2]}\n<b>Ты поставил на победу {split_teams[2]}</b>',
                              parse_mode='HTML')

        with connect('aboba.db') as db:
            cur = db.cursor()
            cur.execute(
                f"UPDATE users SET '{callback.from_user.first_name}' = 'P2' WHERE matches == '{callback.message.text}'")

    else:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                              text=f'В матче: {split_teams[0]} vs {split_teams[2]}\n<b>Ты поставил на ничью</b>',
                              parse_mode='HTML')

        with connect('aboba.db') as db:
            cur = db.cursor()
            cur.execute(
                f"UPDATE users SET '{callback.from_user.first_name}' = 'X' WHERE matches == '{callback.message.text}'")


bot.polling(True)
