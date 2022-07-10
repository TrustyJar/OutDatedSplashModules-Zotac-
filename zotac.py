import requests
from bs4 import BeautifulSoup
import logging
import dotenv
import datetime
import json
import time
import urllib3
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, HardwareType
from fp.fp import FreeProxy
import urllib

logging.basicConfig(filename='sk.log', filemode='a', format='%(asctime)s - %(name)s - %(message)s',
                    level=logging.DEBUG)

software_names = [SoftwareName.CHROME.value]
hardware_type = [HardwareType.MOBILE__PHONE]
user_agent_rotator = UserAgent(
    software_names=software_names, hardware_type=hardware_type)
CONFIG = dotenv.dotenv_values()

proxyObject = FreeProxy(country_id=[CONFIG['LOCATION']], rand=True)

INSTOCK = []


def scrape_main_site():
    """
    Scrape the site and adds each item to an array
    :return:
    """
    items = []
    url = 'https://zotacstore.queue-it.net/afterevent.aspx?c=zotacstore&e=zotacprod43&cid=en-US'
    # s = requests.Session()
    hdrs = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'}
    req = urllib.request.Request(url=url, headers=hdrs)
    response = urllib.request.urlopen(req).read()
    soup = BeautifulSoup(response, 'html.parser')
    # print(soup)
    check = soup.find('span',  {'id': 'lbHeaderH2'})
    items.append([check.text,url])
    return items


def discord_webhook(product_item):
    data = {}
    data["username"] = CONFIG['USERNAME']
    data["avatar_url"] = CONFIG['AVATAR_URL']
    data["embeds"] = []
    embed = {}
    if product_item == 'initial':
        embed["description"] = "Cache Cleared for Zotac Monitor"
    else:
        embed["title"] = 'Queue Ended' if 'The event has ended' in product_item[0] else 'Queue Started'
        embed['description']=f'**Link: **{product_item[1]}'
        embed['url'] = f'{product_item[1]}'
        embed["image"] = {'url': 'https://assets.queue-it.net/static/QueueFront/img/queue-it_logo_c20bdd104f98eb49499434163ebdb42b.png'}

    embed["author"] = {'name': 'https://zotacstore.queue-it.net/', 'url': 'https://zotacstore.queue-it.net//',
                       'icon_url': 'https://assets.queue-it.net/static/QueueFront/img/queue-it_logo_c20bdd104f98eb49499434163ebdb42b.png'}
    embed["color"] = int(CONFIG['COLOUR'])
    embed["footer"] = {'text': 'ZOTAC Monitor',
                       'icon_url': 'https://assets.queue-it.net/static/QueueFront/img/queue-it_logo_c20bdd104f98eb49499434163ebdb42b.png'}
    embed["timestamp"] = str(datetime.datetime.utcnow())
    data["embeds"].append(embed)

    result = requests.post(CONFIG['WEBHOOK'], data=json.dumps(
        data), headers={"Content-Type": "application/json"})

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
        logging.error(msg=err)
    else:
        print("Payload delivered successfully, code {}.".format(result.status_code))
        logging.info("Payload delivered successfully, code {}.".format(
            result.status_code))


def checker(item):
    for product in INSTOCK:
        if product == item:
            return True
    return False


def remove_duplicates(mylist):
    return [list(t) for t in set(tuple(element) for element in mylist)]


def comparitor(item, start):
    if not checker(item):
        INSTOCK.append(item)
        if start == 0:
            discord_webhook(item)


def monitor():
    print('STARTING MONITOR')
    logging.info(msg='Successfully started monitor')
    discord_webhook('initial')
    start = 1

    # headers = {'User-Agent': user_agent_rotator.get_random_user_agent()}
    keywords = CONFIG['KEYWORDS'].split('%')
    while True:
        try:
            items = remove_duplicates(scrape_main_site())
            print(len(items))
            for item in items:
                check = False
                if keywords == '':
                    comparitor(item, start)
                else:
                    for key in keywords:
                        if key.lower() in item[0].lower():
                            check = True
                            break
                    if check:
                        comparitor(item, start)
            time.sleep(float(CONFIG['DELAY']))
            start = 0
        except Exception as e:
            print(f"Exception found '{e}' - Rotating proxy and user-agent")
            logging.error(e)
            headers = {'User-Agent': user_agent_rotator.get_random_user_agent()}
            


if __name__ == '__main__':
    urllib3.disable_warnings()
    monitor()
