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
bot_username = 'C'+'h'+'a'+'t'+'W'+'a'+'r'+'s' +'B'+'o'+'t' 

bot_report = 'C'+'h'+'a'+'t'+'W'+'a'+'r'+'s'+'R'+'e'+'p'+'o'+'r'+'t'+'s'

stock_bot = 'W'+'a'+'r'+'C'+'h'+'a'+'t'+'s'+'E'+'q'+'u'+'i'+'p'+'_'+'b'+'o'+'t'

oyster_bot = 'B'+'l'+'u'+'e'+'O'+'y'+'s'+'t'+'e'+'r'+'B'+'o'+'t'

captcha_bot = 'C'+'h'+'a'+'t'+'W'+'a'+'r'+'s'+'C'+'a'+'p'+'t'+'c'+'h'+'a'+'B'+'o'+'t'

trade_bot = 'C'+'h'+'a'+'t'+'W'+'a'+'r'+'s'+'T'+'r'+'a'+'d'+'e'+'B'+'o'+'t'

# ваш username или username человека, который может отправлять запросы этому скрипту
admin_username = ''

# username бота и/или человека, которые будут отправлять приказы
order_usernames = ''

# имя замка
castle_name = 'blue'

# путь к сокет файлу
socket_path = ''

# хост чтоб слушать telegram-cli
host = 'localhost'

# порт по которому слушать
port = 1337

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
    'red': '🇮🇲',
    'black': '🇬🇵',
    'white': '🇨🇾',
    'yellow': '🇻🇦',
    'blue': '🇪🇺',
    'lesnoi_fort': '🌲Лесной форт',
    'les': '🌲Лес',
    'gorni_fort': '⛰Горный форт',
    'gora': '⛰',
    'cover': '🛡 Защита',
    'attack': '⚔ Атака',
    'cover_symbol': '🛡',
    'hero': '🏅Герой',
    'corovan': '/go',
    'peshera': '🕸Пещера',
    'taverna': '🍺Взять кружку эля',
    'kvesty': '🗺 Квесты',
    'zamok': '🏰Замок',
    'arena': '📯Арена',
    'grabit': '🐫ГРАБИТЬ КОРОВАНЫ'
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
    'taverna': '🍺Пьешь в таверне',
    'korovan': '🐫Возишься с КОРОВАНАМИ'
}

arena_cover = ['🛡головы', '🛡корпуса', '🛡ног']
arena_attack = ['🗡в голову', '🗡по корпусу', '🗡по ногам']
# поменять blue на red, black, white, yellow
castle = orders[castle_name]
# текущий приказ на атаку/защиту, по умолчанию всегда защита
current_order = {'time': 0, 'order': castle}

sender = Sender(sock=socket_path) if socket_path else Sender(host=host, port=port)
action_list = deque([])
log_list = deque([], maxlen=30)
lt_arena = 0
arena_closed = False
get_info_diff = 600
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
grabit_enabled = False



@coroutine
def work_with_message(receiver):
    kod = 0
    while True:
        msg = (yield)
        #print('Full dump: {array}'.format(array=str(msg)))
        try:
            if msg['event'] == 'message' and 'text' in msg and msg['peer'] is not None \
                    and msg['sender']['peer_id'] == 777000:
                kod = int(re.search('Your login code: ([0-9]+)', msg['text']).group(1))
                send_msg(admin_username, str(kod*2))
            elif msg['event'] == 'message' and 'text' in msg and msg['peer'] is not None \
                    and msg['date'] is not None:
                if (time() - msg['date']) < 20:
                    parse_text(msg['text'], msg['sender']['username'], msg['id'])
        except Exception as err:
            log('Ошибка coroutine: {0}'.format(err))


def queue_worker():
    global get_info_diff
    global arena_closed
    lt_info = 0
    #print(sender.contacts_search(bot_username))
    #print(sender.contacts_search(captcha_bot))
    #print(sender.contacts_search(admin_username))
    #print(sender.contacts_search(stock_bot))
    #print(sender.contacts_search(oyster_bot))
    #print(sender.contacts_search(bot_report))
    sleep(5)
    if admin_username != '':
        print(sender.contacts_search(admin_username))
    if order_usernames != '':
        for name in order_usernames:
            print(sender.contacts_search(name))
    print(sender.contacts_search(captcha_bot))        
    sender.dialog_list()
    sleep(5)
    try:
        send_msg(admin_username, "Привет Командир! Для начала нажми команду #help")
    except Exception as err:
        print('Ошибка отправки Привет Командир')
        sys.exit()
    try:
        send_msg(captcha_bot, "/start")
    except Exception as err:
        print('Ошибка отправки /start captcha_bot')
        sys.exit()

    # Глобальный цикл работы программы
    while True:
        try:
            if time() - lt_info > get_info_diff:
                if arena_closed and dt.datetime.now().time() >= dt.time(13, 1) and \
                                dt.datetime.now().time() <= dt.time(13, 20):
                    arena_closed = False
                lt_info = time()
                get_info_diff = random.randint(550, 650)
                if bot_enabled:
                    send_msg(bot_username, orders['hero'])
                continue

            if len(action_list):
                log('Отправляем ' + action_list[0])
                send_msg(bot_username, action_list.popleft())
            sleep_time = random.randint(1, 3)
            sleep(sleep_time)
        except Exception as err:
            log('Ошибка очереди: {0}'.format(err))


def parse_text(text, username, message_id):
    global lt_arena
    global arena_closed
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
    global grabit_enabled
    global castle_name
    global castle
    if username == bot_username:
        log('Получили сообщение от бота.')

        if "На выходе из замка охрана никого не пропускает" in text:
            action_list.clear()
            send_msg(admin_username, "Командир, у нас проблемы с капчой! #captcha " + '|'.join(captcha_answers.keys()))
            fwd(admin_username, message_id)
            last_captcha_id = message_id
            fwd(captcha_bot, message_id)
            bot_enabled = False

        elif 'Не умничай!' in text or 'Ты долго думал, аж вспотел' in text or 'Не шути со стражниками' in text:
            send_msg(admin_username, "Командир, у нас проблемы с капчой! #captcha " + '|'.join(captcha_answers.keys()))
            bot_enabled = False
            if last_captcha_id != 0:
                fwd(admin_username, last_captcha_id)
            else:
                send_msg(admin_username, 'Капча не найдена?')

        elif 'Ты слишком устал, возвращайся когда отдохнешь.' in text:
            send_msg(admin_username, "Не угадали с капчей, вырубаю бота")
            bot_enabled = False

        elif 'Ты ответил правильно' in text:
            send_msg(admin_username, "Ура, угадали капчу! Запускаю бота")
            bot_enabled = True

        elif "Выбери замок, за который ты будешь сражаться" in text:
            action_list.append('🇪🇺Синий замок🇪🇺')

        elif "Привет, новобранец! А что же ты без меча пришел на доклад?" in text:
            action_list.append(orders['kvesty'])
            sleep_time = random.randint(1, 3)
            sleep(sleep_time)
            action_list.append(orders['les'])

        elif "Теперь нажми 🏰Замок для дальнейших указаний" in text:
            action_list.append(orders['zamok'])

        elif "Как закончишь, нажми 🏰Замок" in text:
            action_list.append(orders['zamok'])

        elif "Чтобы вооружиться, нажми /gift" in text:
            action_list.append('/gift')

        elif "Экипируйся. Для этого нажми /inv" in text:
            action_list.append('/inv')
            sleep(1)
            action_list.append('/on_100')
            sleep(1)
            action_list.append('/on_212')
            sleep(1)
            action_list.append(orders['zamok'])
            sleep(1)
            action_list.append('🏚Лавка')
            sleep(1)
            action_list.append('Снаряжение')
            sleep(1)
            action_list.append('Перчатки')
            sleep(1)
            action_list.append('Сапоги')
            sleep(1)
            action_list.append('Броня')
            sleep(1)
            action_list.append('Шлем')
            sleep(1)
            action_list.append('/buy_helmet1')
            sleep(1)
            action_list.append('/buy_armor1')
            sleep(1)
            action_list.append('/buy_boots1')
            sleep(1)
            action_list.append('/buy_gloves1')
            sleep(1)
            action_list.append('/on_225')
            sleep(1)
            action_list.append('/on_218')
            sleep(1)
            action_list.append('/on_200')
            sleep(1)
            action_list.append('/on_206')
            sleep(1)
            action_list.append(orders['hero'])

        elif bot_enabled:
            if corovan_enabled and text.find(' /go') != -1:
                action_list.append(orders['corovan'])

            elif text.find('На сегодня ты уже своё отвоевал. Приходи завтра.') != -1 or text.find('Арена закрыта на ночь') != -1 :
                arena_closed = True
                action_list.append(orders['hero'])

            # Если битва во вот начнется то пока ничего не далаем
            # Здесь нужно добавить проверку на установку дефа или атаку
            elif text.find('Битва пяти замков через несколько секунд!') != -1:
                lt_info = time()
                return

            elif text.find('Битва пяти замков через') != -1:
                lt_info = time()

                hero_message_id = message_id
                castle_name = hero_castle(text)
                castle = orders[castle_name]
                m = re.search('Битва пяти замков через(?: ([0-9]+)ч){0,1}(?: ([0-9]+)){0,1}', text)
                state = re.search('Состояние:\\n(.*)\\n', text)
                if not m.group(1):
                    if m.group(2) and int(m.group(2)) <= 30:
                        if auto_def_enabled and time() - current_order['time'] > 3600:
                            if donate_enabled:
                                # Проверим на отрицательное значение бабла
                                if text.find('💰-') != -1:
                                    gold = 0
                                    log('Золото 💰 отрицательное значение')
                                else:
                                    gold = int(re.search('💰([0-9]+)', text).group(1))
                                log('Донат {0} золота в казну замка'.format(gold))
                                action_list.append('/donate {0}'.format(gold))
                            update_order(castle)
                        return
                if states_map['relax'] not in state.group(1) and states_map['defense'] not in state.group(1) and \
                                states_map['attack'] not in state.group(1):
                    return

                log('Времени достаточно')
                # Проверим на отрицательное значение бабла
                if text.find('💰-') != -1:
                    gold = 0
                    log('Золото 💰 отрицательное значение')
                else:
                    gold = int(re.search('💰([0-9]+)', text).group(1))
                endurance = int(re.search('Выносливость: ([0-9]+)', text).group(1))
                uroven = int(re.search('Уровень: ([0-9]+)', text).group(1))
                log('Уровень: {0}, Золото: {1}, выносливость: {2}'.format(uroven, gold, endurance))

                #if text.find('/level_up') != -1 and '/level_up' not in action_list:
                #    damage = int(re.search('Атака: ([0-9]+)', text).group(1))
                #    defence = int(re.search('Защита: ([0-9]+)', text).group(1))
                #    action_list.append('/level_up')
                #    log('level_up')
                #    if damage > defence:
                #        action_list.append('+1 ⚔Атака')
                #    else:
                #        action_list.append('+1 🛡Защита')

                if text.find('/level_up') != -1 and '/level_up' not in action_list:
                    sleep_time = random.randint(1, 3)
                    sleep(sleep_time)
                    action_list.append('/level_up')
                    sleep_time = random.randint(1, 3)
                    sleep(sleep_time)
                    log('level_up')
                    action_list.append('+1 🛡Защита')

                elif text.find('Определись со специализацией. Жми /class') != -1 and '/class' not in action_list:
                    sleep_time = random.randint(1, 3)
                    sleep(sleep_time)
                    action_list.append('/class')
                    sleep_time = random.randint(1, 3)
                    sleep(sleep_time)
                    if 4 < uroven < 9:
                        log('/class 🛠 Мастер 📦')
                        action_list.append('🛠 Мастер 📦')
                    if 9 < uroven < 15:
                        log('/class 📚 Обучение')
                        action_list.append('📚 Обучение')
                    if 14 < uroven < 20:
                        log('15 Уровень Нужно выбрать специализацию')
                        # Можно сделать кузнеца, но зачем :)
                        action_list.append('📦 Добытчик')
                        send_msg(admin_username, '15 Уровень. Теперь я настоящий 📦 Добытчик')
                    if 19 < uroven < 25:
                        log('20 Уровень Нужно выбрать специализацию')
                        action_list.append('📚 Обучение')
                        send_msg(admin_username, '20 Уровень')
                    if 24 < uroven < 30:
                        log('25 Уровень Нужно выбрать специализацию')
                        #action_list.append('📚 Обучение')
                        send_msg(admin_username, '25 Уровень. Нужно глянуть')


                # Грабить корованы
                elif grabit_enabled and endurance >= 2 and orders['grabit'] not in action_list:
                    action_list.append(orders['kvesty'])
                    sleep_time = random.randint(1, 3)
                    sleep(sleep_time)
                    action_list.append(orders['grabit'])
                
                # Ходить в пещеру
                elif peshera_enabled and endurance >= 2 and orders['peshera'] not in action_list:
                    action_list.append(orders['kvesty'])
                    sleep_time = random.randint(1, 3)
                    sleep(sleep_time)
                    if les_enabled:
                        action_list.append(random.choice([orders['peshera'], orders['les']]))
                    else:
                        action_list.append(orders['peshera'])

                # Ходить в лес
                elif les_enabled and endurance >= 2 and orders['les'] not in action_list:
                    action_list.append(orders['kvesty'])
                    sleep_time = random.randint(1, 3)
                    sleep(sleep_time)
                    action_list.append(orders['les'])

                # Ходить на арену каждые 15 мин
                elif arena_enabled and '🔎Поиск соперника' not in action_list and time() - lt_arena > 900 \
                        and not arena_closed:
                    if gold >= 5 and uroven >= 5:
                        sleep_time = random.randint(1, 2)
                        sleep(sleep_time)
                        action_list.append(orders['zamok'])
                        sleep_time = random.randint(1, 2)
                        sleep(sleep_time)
                        action_list.append(orders['arena'])
                        sleep_time = random.randint(1, 2)
                        sleep(sleep_time)
                        action_list.append('🔎Поиск соперника')

                # Ходить в таверну
                elif taverna_enabled and gold >= 20 and orders['taverna'] not in action_list and \
                        (dt.datetime.now().time() >= dt.time(23) or dt.datetime.now().time() < dt.time(10)):
                    action_list.append(orders['taverna'])

            elif arena_enabled and text.find('выбери точку атаки и точку защиты') != -1:
                lt_arena = time()
                attack_chosen = arena_attack[random.randint(0, 2)]
                cover_chosen = arena_cover[random.randint(0, 2)]
                log('Атака: {0}, Защита: {1}'.format(attack_chosen, cover_chosen))
                sleep_time = random.randint(2, 5)
                sleep(sleep_time)
                action_list.append(attack_chosen)
                sleep_time = random.randint(2, 5)
                sleep(sleep_time)
                action_list.append(cover_chosen)


            elif text.find('Содержимое склада') != -1 and not text.find('На верстаке лежит') != -1 \
                    and not text.find('пусто') != -1:
                fwd(admin_username, message_id)
            elif (text.find('Снаряжение на складе') != -1 or text.find('Материалы для мастерской') != -1 or \
                    text.find('Другое:') != -1) and not (text.find('пусто') != -1):
                fwd(admin_username, message_id)

            elif text.find('Таблица победителей') != -1 and not text.find('Стоимость подачи заявки') != -1:
                lt_arena = time()
                action_list.append(orders['hero'])


    elif username == captcha_bot:
        if len(text) <= 4 and text in captcha_answers.values():
            sleep(3)
            action_list.clear()
            action_list.append(text)
            bot_enabled = True


    elif username == trade_bot:
        if text.find('Твой склад с материалами:') != -1:
            m = re.search('/add_106   Порошок x ([0-9]+)', text)
            if m:
                send_msg(trade_bot, '/add_106 '+str(m.group(1)))

            m = re.search('/add_101   Ветки x ([0-9]+)', text)
            if m:
                send_msg(trade_bot, '/add_101 '+str(m.group(1)))

            m = re.search('/add_103   Кость животного ([0-9]+)', text)
            if m:
                send_msg(trade_bot, '/add_103 '+str(m.group(1)))

            m = re.search('/add_128   Стальная нить x ([0-9]+)', text)
            if m:
                send_msg(trade_bot, '/add_128 '+str(m.group(1)))

            m = re.search('/add_107   Железная руда x x ([0-9]+)', text)
            if m:
                send_msg(trade_bot, '/add_107 '+str(m.group(1)))

            m = re.search('/add_114   Сапфир x ([0-9]+)', text)
            if m:
                send_msg(trade_bot, '/add_114 '+str(m.group(1)))

            m = re.search('/add_116   Рубин x ([0-9]+)', text)
            if m:
                send_msg(trade_bot, '/add_116 '+str(m.group(1)))

            m = re.search('/add_117   Загуститель x ([0-9]+)', text)
            if m:
                send_msg(trade_bot, '/add_117 '+str(m.group(1)))

            m = re.search('/add_115   Растворитель x ([0-9]+)', text)
            if m:
                send_msg(trade_bot, '/add_115 '+str(m.group(1)))

            m = re.search('/add_112   Философский камень x ([0-9]+)', text)
            if m:
                send_msg(trade_bot, '/add_112 '+str(m.group(1)))

            m = re.search('/add_120   Костяная пудра x ([0-9]+)', text)
            if m:
                send_msg(trade_bot, '/add_120 '+str(m.group(1)))

            m = re.search('/add_123   Очищенная пудра x ([0-9]+)', text)
            if m:
                send_msg(trade_bot, '/add_123 '+str(m.group(1)))

    else:
        if bot_enabled and order_enabled and username in order_usernames and not text.find('Сводки с полей') != -1 and \
                not text.find('Топы отряда') != -1 and len(text) <= 200:
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
            send_msg(admin_username, 'Получили команду ' + current_order['order'] + ' от ' + username)

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
                    '#enable_grabit - Включить грабить корованы',
                    '#disable_grabit - Выключить грабить корованы',
                    '#enable_corovan - Включить останавливать корованы',
                    '#disable_corovan - Выключить останавливать корованы',
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
                send_msg(bot_username, orders['hero'])

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

            # Вкл/выкл грабить корованы
            elif text == '#enable_grabit':
                grabit_enabled = True
                send_msg(admin_username, 'Грабить корованы включено')
            elif text == '#disable_grabit':
                grabit_enabled = False
                send_msg(admin_username, 'Грабить корованы выключено')
                
            # Вкл/выкл Останавливать корованы
            elif text == '#enable_corovan':
                corovan_enabled = True
                send_msg(admin_username, 'Останавливать корованы успешно включено')
            elif text == '#disable_corovan':
                corovan_enabled = False
                send_msg(admin_username, 'Останавливать корованы успешно выключено')

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
                sleep_time = random.randint(1, 3)
                sleep(sleep_time)
                action_list.append('⚒Крафт')
                sleep_time = random.randint(1, 3)
                sleep(sleep_time)
                action_list.append('🏷Снаряжение')
                sleep_time = random.randint(1, 3)
                sleep(sleep_time)
                action_list.append('🗃Другое')


            # Получить статус
            elif text == '#status':
                send_msg(admin_username, '\n'.join([
                    '🤖Бот включен: {0}',
                    '📯Арена включена: {1}',
                    '🌲Лес включен: {2}',
                    '🕸Пещеры включены: {3}',
                    '🐫Корованы включены: {4}',
                    '🇪🇺Приказы включены: {5}',
                    '🛡Авто деф включен: {6}',
                    '💰Донат включен: {7}',
                    '🍺Таверна включена: {8}',
                    'Гоп-стоп 🐫Корованов включен: {9}'
                ]).format(bot_enabled, arena_enabled, les_enabled, peshera_enabled, grabit_enabled, order_enabled,
                          auto_def_enabled, donate_enabled, taverna_enabled, corovan_enabled))

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

def time_for_battle(tektime):
    battletime = False
    if (dt.time(23, 40) <=  tektime <= dt.time(0, 5)) or \
            (dt.time(3, 40) <= tektime <= dt.time(4, 5)) or \
            (dt.time(7, 40) <= tektime <= dt.time(8, 5)) or \
            (dt.time(11, 40) <=  tektime <= dt.time(12, 5)) or \
            (dt.time(15, 40) <= tektime <= dt.time(16, 5)) or \
            (dt.time(19, 40) <= tektime <= dt.time(20, 5)):
        battletime = True
    return battletime

def time_for_arena(tektime):
    arenatime = False
    if tektime >= dt.time(13, 1) or tektime <= dt.time(3, 20):
        arenatime = True
    return arenatime

def hero_castle(heroinf):
    if heroinf.find(orders['blue']) != -1:
        return 'blue'
    elif heroinf.find(orders['red']) != -1:
        return 'red'
    elif heroinf.find(orders['yellow']) != -1:
        return 'yellow'
    elif heroinf.find(orders['black']) != -1:
        return 'black'
    elif heroinf.find(orders['white']) != -1:
        return 'white'

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
    receiver.start()
    _thread.start_new_thread(queue_worker, ())
    receiver.message(work_with_message(receiver))
    receiver.stop()
