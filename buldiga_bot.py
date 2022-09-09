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
    date = data.findAll('span', class_='sct')

    res_team1 = list()
    res_date = list()

    for i in team1:
        i = i.text.replace('\n', '')
        res_team1.append(i)

    for i in team2:
        i = i.text.replace('\n', '')
        res_team1.append(i)

    for i in date:
        i = i.text.replace('\n', '')
        res_date.append(i)

    a = 0

    res_blyat = list()

    for i in range(len(res_team1) // 2):
        res_blyat.append(f'{res_team1[a]} vs {res_team1[a + (len(res_team1) // 2)]} (Дата: {res_date[a][0:10]})')
        a += 1
    return res_blyat


@bot.message_handler(commands=['start'])
def start(message):
    general_keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    matches = types.KeyboardButton(text='Показать матчи')
    help = types.KeyboardButton(text='🆘 Подсказка 🆘')
    general_keyboard.add(matches, help)
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


@bot.message_handler(func=lambda x: x.text == '🆘 Подсказка 🆘')
def help(message):
    bot.send_message(message.chat.id,
                     'Если ты не знаешь на кого ставить и тебе необходима помощь специально обученной нейросети, то просто напиши список команд через запятую и я подскажу тебе!\n(Пример записи: Team Spirit, Fnatic)')
    bot.register_next_step_handler(message, help_answer)


def help_answer(message):
    general_keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    matches = types.KeyboardButton(text='Показать матчи')
    help = types.KeyboardButton(text='🆘 Подсказка 🆘')
    general_keyboard.add(matches, help)
    list_answer = message.text.split(',')
    answer = choice(list_answer)
    bot.send_message(message.chat.id, f'Я бы на твоем месте поставил на <b>{answer}</b>', parse_mode='HTML',
                     reply_markup=general_keyboard)


@bot.message_handler(func=lambda x: x.text == 'Показать матчи')
def view_matches(message):
    sum_matches = 0
    sum_bets = 0
    with connect('aboba.db') as db:
        cur = db.cursor()
        for i in cur.execute("SELECT count(matches) FROM users"):
            for j in i:
                sum_matches += j

        for i in cur.execute(f"SELECT count({message.from_user.first_name}) FROM users"):
            for j in i:
                sum_bets += j

    if sum_matches != sum_bets or (sum_matches == 0 and sum_bets == 0):
        try:
            for i in parse_matches():
                if 'TBD' in i:
                    continue
                else:
                    choice_keyboard = types.InlineKeyboardMarkup(row_width=3)
                    left = types.InlineKeyboardButton(text='П1',
                                                      callback_data='p1')
                    right = types.InlineKeyboardButton(text='П2',
                                                       callback_data='p2')
                    drow = types.InlineKeyboardButton(text='X',
                                                      callback_data='x')
                    choice_keyboard.add(left, drow, right)
                    bot.send_message(message.chat.id, i, reply_markup=choice_keyboard)

            with connect('aboba.db') as db:
                cur = db.cursor()

                a = cur.execute('SELECT matches FROM users')
                a = a.fetchall()
                db = list()
                for i in a:
                    for j in i:
                        db.append(j)

                for i in parse_matches():
                    if 'TBD' in i:
                        continue
                    elif i not in db:
                        cur.execute(f"INSERT INTO users (matches) VALUES ('{i}')")
        except IndexError:
            bot.send_message(message.chat.id,
                             'К сожалению игра уже началась(\nДождитесь окончания матча и попробуйте снова')
    else:
        bot.send_message(message.chat.id, 'Ставки сделаны, ставок больше нет!')


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
