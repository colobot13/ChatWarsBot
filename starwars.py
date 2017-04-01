# coding=utf-8
from pytg.sender import Sender
from pytg.receiver import Receiver
from pytg.utils import coroutine
from collections import deque
from time import time, sleep
from getopt import getopt
import sys
import datetime as dt
import re
import _thread
import random

# username игрового бота
bot_username = 'ChatWarsBot'

stock_bot = 'WarChatsEquip_bot'

# ваш username или username человека, который может отправлять запросы этому скрипту
admin_username = 'colobot13'

# username бота и/или человека, которые будут отправлять приказы
order_usernames = 'colobot13'

# имя замка
castle_name = 'blue'

captcha_bot = 'ChatWarsCaptchaBot'

# путь к сокет файлу
socket_path = ''

# хост чтоб слушать telegram-cli
host = 'localhost'

# порт по которому слушать
port = 1338

opts, args = getopt(sys.argv[1:], 'a:o:c:s:h:p', ['admin=', 'order=', 'castle=', 'socket=', 'host=', 'port='])

for opt, arg in opts:
    if opt in ('-a', '--admin'):
        admin_username = arg
    elif opt in ('-o', '--order'):
        order_usernames = arg.split(',')
    elif opt in ('-c', '--castle'):
        castle_name = arg
    elif opt in ('-s', '--socket'):
        socket_path = arg
    elif opt in ('-h', '--host'):
        host = arg
    elif opt in ('-p', '--port'):
        port = int(arg)

orders = {
    'red': '⭕',
    'black': '⚫',
    'white': '🌐',
    'yellow': '☠',
    'blue': '⚖',
    'lesnoi_fort': '🛢Научный центр',
    'les': '🛰Помочь кораблю',
    'gorni_fort': '💎Ресурсный центр',
    #'gora': '⛰',
    'cover': '🎚Оборона',
    'attack': '💣Нападение',
    #'cover_symbol': '🛡',
    'hero': '👨‍🚀 Пилот',
    'corovan': '/go',
    'peshera': '🔎Изучить планету',
    'taverna': '🍺Взять кружку эля',
    'kvesty': '⌨️ Терминал'

}

captcha_answers = {
    'watermelon_n_cherry': '🍉🍒',
    'bread_n_cheese': '🍞🧀',
    'cheese': '🧀',
    'pizza': '🍕',
    'hotdog': '🌭',
    'eggplant_n_carrot': '🍆🥕',
    'dog': '🐕',
    'horse': '🐎',
    'goat': '🐐',
    'cat': '🐈',
    'pig': '🐖',
    'squirrel': '🐿'
}

states_map = {
    'relax': '🛌Отдых',
    'defense': '🛡Защита',
    'attack': '⚔Атака',
    'arena': '📯На арене',
    'les': '🌲В лесу',
    'peshera': '🕸В пещере',
    'taverna': '🍺Пьешь в таверне'
}

arena_cover = ['🛡головы', '🛡корпуса', '🛡ног']
arena_attack = ['🗡в голову', '🗡по корпусу', '🗡по ногам']
# поменять blue на red, black, white, yellow в зависимости от вашего замка
castle = orders[castle_name]
# текущий приказ на атаку/защиту, по умолчанию всегда защита, трогать не нужно
current_order = {'time': 0, 'order': castle}

sender = Sender(sock=socket_path) if socket_path else Sender(host=host, port=port)
action_list = deque([])
log_list = deque([], maxlen=30)
lt_arena = 0
get_info_diff = 360
hero_message_id = 0
last_captcha_id = 0

bot_enabled = True
arena_enabled = True
taverna_enabled = False
les_enabled = True
peshera_enabled = False
corovan_enabled = True
order_enabled = True
auto_def_enabled = True
donate_enabled = False


@coroutine
def work_with_message(receiver):
    while True:
        msg = (yield)
        try:
            if msg['event'] == 'message' and 'text' in msg and msg['peer'] is not None:
                parse_text(msg['text'], msg['sender']['username'], msg['id'])
        except Exception as err:
            log('Ошибка coroutine: {0}'.format(err))


def queue_worker():
    global get_info_diff
    lt_info = 0
    # гребаная магия
    print(sender.contacts_search(bot_username))
    print(sender.contacts_search(captcha_bot))
    print(sender.contacts_search(admin_username))
    print(sender.contacts_search(stock_bot))
    #sender.dialog_list()
    sleep(3)
    while True:
        try:

            if time() - lt_info > get_info_diff:
                lt_info = time()
                get_info_diff = random.randint(300, 500)
                if bot_enabled:
                    send_msg(bot_username, orders['hero'])
                continue

            if len(action_list):
                log('Отправляем ' + action_list[0])
                send_msg(bot_username, action_list.popleft())
            sleep_time = random.randint(2, 6)
            sleep(sleep_time)
        except Exception as err:
            log('Ошибка очереди: {0}'.format(err))


def parse_text(text, username, message_id):
    global lt_arena
    global lt_info
    global hero_message_id
    global bot_enabled
    global arena_enabled
    global taverna_enabled
    global les_enabled
    global peshera_enabled
    global corovan_enabled
    global order_enabled
    global auto_def_enabled
    global donate_enabled
    global last_captcha_id
    if username == bot_username:
        log('Получили сообщение от бота. Проверяем условия')

        if "На выходе из замка охрана никого не пропускает" in text:
            log('На выходе из замка охрана никого не пропускает')
            with open('captcha.txt', 'a+') as f:
                f.seek(0)
                for line in f:
                    if text in line:
                        break
                else:
                    f.write(text + '\n' + '-' * 8 + '\n')

            action_list.clear()
            send_msg(admin_username, "Командир, у нас проблемы с капчой! #captcha " + '|'.join(captcha_answers.keys()))
            fwd(admin_username, message_id)
            last_captcha_id = message_id
            fwd(captcha_bot, message_id)
            bot_enabled = False

        elif 'Не умничай!' in text or 'Ты долго думал, аж вспотел от напряжения' in text or 'Не шути со стражниками' in text:
            log('Командир, у нас проблемы с капчой!')
            send_msg(admin_username, "Командир, у нас проблемы с капчой! #captcha " + '|'.join(captcha_answers.keys()))
            bot_enabled = False
            if last_captcha_id != 0:
                fwd(admin_username, last_captcha_id)
            else:
                send_msg(admin_username, 'Капча не найдена?')

        elif 'Ты слишком устал, возвращайся когда отдохнешь.' in text:
            log('Не угадали с капчей, вырубаю бота')
            send_msg(admin_username, "Не угадали с капчей, вырубаю бота")
            bot_enabled = False

        elif 'Ты ответил правильно' in text:
            log('Ура, угадали капчу! Запускаю бота')
            send_msg(admin_username, "Ура, угадали капчу! Запускаю бота")
            bot_enabled = True

        if bot_enabled:
            log('Бот включен')
            if corovan_enabled and text.find(' /go') != -1:
                log('Ловлю корован')
                action_list.append(orders['corovan'])

            elif text.find('Сражаться можно не чаще чем один раз в час.') != -1:
                log('Сражаться можно не чаще чем один раз в час.')
                lt_arena = time()
                lt_info = time()
                action_list.append(orders['hero'])

            elif text.find('Космическая битва через') != -1:
                log('Космическая битва через ? что ха хрень')
                hero_message_id = message_id
                log(hero_message_id)
                m = re.search('Космическая битва через(?: ([0-9]+)ч){0,1}(?: ([0-9]+)){0,1}', text)
                log(m)
                state = re.search('Статус:\\n(.*)\\n', text)
                log(state)
                if not m.group(1):
                    log('if not m.group(1)')
                    log(m.group(1))
                    if m.group(2) and int(m.group(2)) <= 30:
                        if auto_def_enabled and time() - current_order['time'] > 3600:
                            if donate_enabled:
                                gold = int(re.search('💴([0-9]+)', text).group(1))
                                log('Донат {0} золота в казну замка'.format(gold))
                                action_list.append('/donate {0}'.format(gold))
                            update_order(castle)
                        return
                if states_map['relax'] not in state.group(1) and states_map['defense'] not in state.group(1) and \
                                states_map['attack'] not in state.group(1):
                    return

                log('Времени достаточно')
                gold = int(re.search('💴([0-9]+)', text).group(1))
                endurance = int(re.search('Топливо: ([0-9]+)', text).group(1))
                log('Золото: {0}, выносливость: {1}'.format(gold, endurance))

                #if text.find('/level_up') != -1 and '/level_up' not in action_list:
                #    damage = int(re.search('Атака: ([0-9]+)', text).group(1))
                #    defence = int(re.search('Защита: ([0-9]+)', text).group(1))
                #    action_list.append('/level_up')
                #    log('level_up')
                #    if damage > defence:
                #        action_list.append('+1 ⚔Атака')
                #    else:
                #        action_list.append('+1 🛡Защита')

                if peshera_enabled and endurance >= 2 and orders['peshera'] not in action_list:
                    action_list.append(orders['kvesty'])
                    sleep(2)
                    action_list.append(orders['peshera'])

                elif les_enabled and endurance >= 2 and orders['les'] not in action_list:
                    action_list.append(orders['kvesty'])
                    sleep(2)
                    action_list.append(orders['les'])

                elif arena_enabled and gold >= 5 and '🔎Поиск соперника' not in action_list and time() - lt_arena > 3600:
                    action_list.append('🔎Поиск соперника')

                elif taverna_enabled and gold >= 20 and orders['taverna'] not in action_list and \
                        (dt.datetime.now().time() >= dt.time(19) or dt.datetime.now().time() < dt.time(6)):
                    action_list.append(orders['taverna'])

            elif arena_enabled and text.find('выбери точку атаки и точку защиты') != -1:
                lt_arena = time()
                attack_chosen = arena_attack[random.randint(0, 2)]
                cover_chosen = arena_cover[random.randint(0, 2)]
                log('Атака: {0}, Защита: {1}'.format(attack_chosen, cover_chosen))
                action_list.append(attack_chosen)
                action_list.append(cover_chosen)

            elif text.find('Содержимое склада') != -1:
                fwd(stock_bot, message_id)

            elif "Хорошо!" not in text and "Хороший план" not in text and "5 минут" not in text and \
                            "Ошибка направления команды терминалу" not in text and "Солнечный ветер завывает" not in text and \
                            "Соперник найден" not in text and "Синий замок" not in text and \
                            "Синего замка" not in text and "Общение внутри фракции" not in text and \
                            "Победил пилот" not in text and not re.findall(r'\bнанес\b(.*)\bудар\b', s):
                #with open('taverna.txt', 'a+') as f:
                #    f.seek(0)
                #    for line in f:
                #        if text[0:8] in line:
                #            break
                #    else:
                #        f.write(text + '\n')
                action_list.append(orders['hero'])
                lt_info = time()

    elif username == 'ChatWarsCaptchaBot':
        if len(text) <= 4 and text in captcha_answers.values():
            sleep(3)
            action_list.clear()
            action_list.append(text)
            bot_enabled = True

    else:
        if bot_enabled and order_enabled and username in order_usernames:
            if text.find(orders['red']) != -1:
                update_order(orders['red'])
            elif text.find(orders['black']) != -1:
                update_order(orders['black'])
            elif text.find(orders['white']) != -1:
                update_order(orders['white'])
            elif text.find(orders['yellow']) != -1:
                update_order(orders['yellow'])
            elif text.find(orders['blue']) != -1:
                update_order(orders['blue'])
            elif text.find('🌲') != -1:
                update_order(orders['lesnoi_fort'])
            elif text.find('⛰') != -1:
                update_order(orders['gorni_fort'])
            elif text.find('🛡') != -1:
                update_order(castle)

                # send_msg(admin_username, 'Получили команду ' + current_order['order'] + ' от ' + username)

        if username == admin_username:
            if text == '#help':
                send_msg(admin_username, '\n'.join([
                    '#enable_bot - Включить бота',
                    '#disable_bot - Выключить бота',
                    '#enable_arena - Включить арену',
                    '#disable_arena - Выключить арену',
                    '#disable_taverna - Выключить таверну',
                    '#enable_taverna - Влючить таверну',
                    '#enable_les - Включить лес',
                    '#disable_les - Выключить лес',
                    '#enable_peshera - Включить пещеры',
                    '#disable_peshera - Выключить пещеры',
                    '#enable_corovan - Включить корован',
                    '#disable_corovan - Выключить корован',
                    '#enable_order - Включить приказы',
                    '#disable_order - Выключить приказы',
                    '#enable_auto_def - Включить авто деф',
                    '#disable_auto_def - Выключить авто деф',
                    '#enable_donate - Включить донат',
                    '#disable_donate - Выключить донат',
                    '#update_stock - обновить сток',
                    '#status - Получить статус',
                    '#hero - Получить информацию о герое',
                    '#push_order - Добавить приказ ({0})'.format(','.join(orders)),
                    '#order - Дебаг, последняя команда защиты/атаки замка',
                    '#log - Дебаг, последние 30 сообщений из лога',
                    '#time - Дебаг, текущее время',
                    '#lt_arena - Дебаг, последняя битва на арене',
                    '#get_info_diff - Дебаг, последняя разница между запросами информации о герое',
                    '#ping - Дебаг, проверить жив ли бот',
                ]))

            # Вкл/выкл бота
            elif text == '#enable_bot':
                bot_enabled = True
                send_msg(admin_username, 'Бот успешно включен')
            elif text == '#disable_bot':
                bot_enabled = False
                send_msg(admin_username, 'Бот успешно выключен')

            # Вкл/выкл арены
            elif text == '#enable_arena':
                arena_enabled = True
                send_msg(admin_username, 'Арена успешно включена')
            elif text == '#disable_arena':
                arena_enabled = False
                send_msg(admin_username, 'Арена успешно выключена')

            # Вкл/выкл таверны
            elif text == '#enable_taverna':
                taverna_enabled = True
                send_msg(admin_username, 'Таверна успешно включена')
            elif text == '#disable_taverna':
                taverna_enabled = False
                send_msg(admin_username, 'Таверна успешно выключена')

            # Вкл/выкл леса
            elif text == '#enable_les':
                les_enabled = True
                send_msg(admin_username, 'Лес успешно включен')
            elif text == '#disable_les':
                les_enabled = False
                send_msg(admin_username, 'Лес успешно выключен')

            # Вкл/выкл пещеры
            elif text == '#enable_peshera':
                peshera_enabled = True
                send_msg(admin_username, 'Пещера успешно включена')
            elif text == '#disable_peshera':
                peshera_enabled = False
                send_msg(admin_username, 'Пещера успешно выключена')

            # Вкл/выкл корована
            elif text == '#enable_corovan':
                corovan_enabled = True
                send_msg(admin_username, 'Корованы успешно включены')
            elif text == '#disable_corovan':
                corovan_enabled = False
                send_msg(admin_username, 'Корованы успешно выключены')

            # Вкл/выкл команд
            elif text == '#enable_order':
                order_enabled = True
                send_msg(admin_username, 'Приказы успешно включены')
            elif text == '#disable_order':
                order_enabled = False
                send_msg(admin_username, 'Приказы успешно выключены')

            # Вкл/выкл авто деф
            elif text == '#enable_auto_def':
                auto_def_enabled = True
                send_msg(admin_username, 'Авто деф успешно включен')
            elif text == '#disable_auto_def':
                auto_def_enabled = False
                send_msg(admin_username, 'Авто деф успешно выключен')

            # Вкл/выкл авто донат
            elif text == '#enable_donate':
                donate_enabled = True
                send_msg(admin_username, 'Донат успешно включен')
            elif text == '#disable_donate':
                donate_enabled = False
                send_msg(admin_username, 'Донат успешно выключен')

            elif text == '#update_stock':
                action_list.append('/stock')

            # Получить статус
            elif text == '#status':
                send_msg(admin_username, '\n'.join([
                    'Бот включен: {0}',
                    'Арена включена: {1}',
                    'Лес включен: {2}',
                    'Пещера включена: {3}',
                    'Корованы включены: {4}',
                    'Приказы включены: {5}',
                    'Авто деф включен: {6}',
                    'Донат включен: {7}',
                    'Таверна включена: {8}'
                ]).format(bot_enabled, arena_enabled, les_enabled, peshera_enabled, corovan_enabled, order_enabled,
                          auto_def_enabled, donate_enabled, taverna_enabled))

            # Информация о герое
            elif text == '#hero':
                if hero_message_id == 0:
                    send_msg(admin_username, 'Информация о герое пока еще недоступна')
                else:
                    fwd(admin_username, hero_message_id)

            # Получить лог
            elif text == '#log':
                send_msg(admin_username, '\n'.join(log_list))
                log_list.clear()

            elif text == '#lt_arena':
                send_msg(admin_username, str(dt.datetime.fromtimestamp(lt_arena).time()))

            elif text == '#order':
                text_date = str(dt.datetime.fromtimestamp(current_order['time']).time())
                send_msg(admin_username, current_order['order'] + ' ' + text_date)

            elif text == '#time':
                text_date = str(dt.datetime.now().time())
                send_msg(admin_username, text_date)

            elif text == '#ping':
                send_msg(admin_username, '#pong')

            elif text == '#get_info_diff':
                send_msg(admin_username, str(get_info_diff))

            elif text.startswith('#push_order'):
                command = text.split(' ')[1]
                if command in orders:
                    update_order(orders[command])
                    send_msg(admin_username, 'Команда ' + command + ' применена')
                else:
                    send_msg(admin_username, 'Команда ' + command + ' не распознана')

            elif text.startswith('#captcha'):
                command = text.split(' ')[1]
                if command in captcha_answers:
                    action_list.clear()
                    action_list.append(captcha_answers[command])
                    bot_enabled = True
                    send_msg(admin_username, 'Команда ' + command + ' применена')
                else:
                    send_msg(admin_username, 'Команда ' + command + ' не распознана')


def send_msg(to, message):
    sender.mark_read('@' + to)
    sender.send_msg('@' + to, message)


def fwd(to, message_id):
    sender.fwd('@' + to, message_id)


def update_order(order):
    current_order['order'] = order
    current_order['time'] = time()
    if order == castle:
        action_list.append(orders['cover'])
    else:
        action_list.append(orders['attack'])
    action_list.append(order)


def log(text):
    message = '{0:%Y-%m-%d %H:%M:%S}'.format(dt.datetime.now()) + ' ' + text
    print(message)
    log_list.append(message)


if __name__ == '__main__':
    receiver = Receiver(sock=socket_path) if socket_path else Receiver(port=port)
    receiver.start()  # start the Connector.
    _thread.start_new_thread(queue_worker, ())
    receiver.message(work_with_message(receiver))
    receiver.stop()
