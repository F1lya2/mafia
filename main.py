from telebot import TeleBot
import os
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from db import *
from random import choice
from time import sleep


token = '7407551585:AAEqBB4Wk51v50Jiy9PnnBESvnrRgUn1ju8'
bot = TeleBot(token)
game = False
night = False


if not os.path.exists("db.db"):
    create_tabels()

def get_killed(night: bool) -> str:
    if not night:
        u_killed = citizen_kill()
        return f"Горожане выгнали: {u_killed}"
    u_killed = mafia_kill()
    return f"Мафия убила: {u_killed}"


def autoplay_mafia() -> None:
    player_roles = get_players_roles()
    for player_id, role in player_roles:
        usernames = get_all_alive()
        name = f"bot_{player_id}"
        if player_id < 4 and name in usernames and role == "mafia":
            usernames.remove(name)
            vote_username = choice(usernames)
            vote("mafia_vote", vote_username, player_id)

def autoplay_citizen(message: Message):
    player_roles = get_players_roles()
    for player_id, _ in player_roles:
        usernames = get_all_alive()
        name  = f"bot_{player_id}"
        if player_id < 5 and name in usernames:
            usernames.remove(name)
            vote_username = choice(usernames)
            vote("citizen_vote", vote_username, player_id)
            bot.send_message(message.chat.id, f"{name} проголосовал против {vote_username}")
            sleep(0.5)


def game_loop(message: Message):
    global game, night
    bot.send_message(message.chat.id, "Добро пожаловать в игру! Вам дается 2 минуты, чтобы познакомиться с игроками")
    sleep(5)
    while True:
        msg = get_killed(night)
        bot.send_message(message.chat.id, msg)
        if not night:
            bot.send_message(message.chat.id, "Город засыпает, просыпается мафия. Наступила ночь")
        else:
            bot.send_message(message.chat.id, "Город просыпается. Наступает день")
        winner = check_winner()
        if winner == "Мафия" or winner == "Горожане":
            game = False
            bot.send_message(message.chat.id, f"Игра окончена, победители {winner}")
            return
        clear(dead=False)
        night = not night
        alive = get_all_alive()
        alive = "\n".join(alive)
        bot.send_message(message.chat.id, f"В игре:\n{alive}")
        sleep(5)
        autoplay_mafia() if night else autoplay_citizen(message)




@bot.message_handler(func=lambda message: message.text.lower() == "готов", chat_types=["private"])
def send_text(message: Message):
    bot.send_message(message.chat.id, f"{message.from_user.first_name} играет!", reply_markup=ReplyKeyboardRemove())
    if get_user(message.from_user.id):
        bot.send_message(message.chat.id, "Вы уже есть")
    else:
        bot.send_message(message.chat.id, "Вы добавлены в игру!")
        insert_player(message.from_user.id, message.from_user.first_name)


@bot.message_handler(commands = ['start'])
def game_on(message: Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
    keyboard.add(KeyboardButton("готов"))
    bot.send_message(message.chat.id, "Если хотите играть в игру, нажмите кнопку в лс", reply_markup=keyboard)


@bot.message_handler(commands = ['game'])
def game_start(message: Message):
    global game
    players = players_amount()
    if players >= 5 and not game:
        set_roles(players)
        players_role = get_players_roles()
        mafia_usernames = get_mafia_usernames()
        for player_id, role in players_role:
            try:
                bot.send_message(player_id, role)
                if role == 'mafia':
                    bot.send_message(player_id, f"Все члены мафии:\n {mafia_usernames}")
            except:
                print(f"ID: {player_id}\n ROLE: {role}")
                continue           
        game = True
        clear(dead = True)
        bot.send_message(message.chat.id, "Игра началась!")
        game_loop(message)
        return
    bot.send_message(message.chat.id, "Недостаточно людей!")
    for i in range(5):
        bot_name = f"bot_{i}"
        insert_player(i, bot_name)
        bot.send_message(message.chat.id, f"{bot_name}добавлен")
        sleep(0.2)
    game_start(message)


@bot.message_handler(commands=["kick"])
def kick(message: Message):
    username = " ".join(message.text.split(" ")[1:])
    usernames = get_all_alive()
    if not night:
        if not username in usernames:
            bot.send_message(message.chat.id, "Такого пользователя нет.")
            return
        voted = vote("citizen_vote", username, message.from_user.id)
        if voted:
            bot.send_message(message.chat.id, "Ваш голос учтён.")
            return
        bot.send_message(message.chat.id, "У вас больше нет права голосовать.")
    bot.send_message(message.chat.id, "Сейчас ночь. Вы не можете голосовать за кого-то.")

@bot.message_handler(commands=["kill"])
def kill(message: Message):
    username = " ".join(message.text.split(" ")[1:])
    usernames = get_all_alive()
    mafia_usernames = get_mafia_usernames()
    if night and message.from_user.first_name in mafia_usernames:
        if not username in usernames:
            bot.send_message(message.chat.id, "Такого пользователя нет.")
            return
        voted = vote("mafia_vote", username, message.from_user.id)
        if voted:
            bot.send_message(message.chat.id, "Ваш голос учтён.")
            return
        bot.send_message(message.chat.id, "У вас больше нет права голосовать.")
        return
    bot.send_message(message.chat.id, "Сейчас день. Вы не можете убивать.")





if __name__ == '__main__':
    bot.polling(non_stop = True)
    