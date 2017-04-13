import os
import yaml

with open('users_config.yaml', 'r') as f:
    config = (yaml.load(f))

for d in config:
    for user in d:
        os.system('/home/telegram-cli --json -d -c /home/telegram.config -P ' + str(d[user]['port']) + ' -p ' + user + ' > /dev/null &' )
        os.system('python3 /home/main_twink.py --admin ' + d[user]['admin'] + ' --order '+ d[user]['order'] + \
                ' --port ' + str(d[user]['port']) + ' > /dev/null &')
