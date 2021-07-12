"""Bot to check for estia availability"""
import datetime
import json
import os
import random
import time

import requests
import selenium.webdriver as webdriver
import twilio.rest as twilio_rest


TWILIO_ACCOUNT = os.environ.get('TWILIO_ACCOUNT')
TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER')
MY_NUMBER = os.environ.get('MY_NUMBER')
ALT_MY_NUMBER = os.environ.get('ALT_MY_NUMBER')
HOME = os.environ.get('HOME')


# if this file is present, it means a twilio msg was sent.
# delete to let the script run again. This avoids spamming until we verify
# and acknowledge the notification by deleting the file
CHECK_ONE = f'{HOME}/check_one.log'
CHECK_TWO = f'{HOME}/check_two.log'
GENERIC_COUNT = f'{HOME}/count.json'

URL = 'https://estiaatlakewoodranch.prospectportal.com/bradenton/estia-at-lakewood-ranch/conventional/'
ONE_BED_XPATH = '/html/body/div[1]/div/section/section/div[2]/ul[1]/li[1]/a/span[1]'
TWO_BED_XPATH = '/html/body/div[1]/div/section/section/div[2]/ul[1]/li[2]/a/span[1]'
GET_NOTIFIED_ONE_BR_XPATH = '/html/body/div/div/section/section/div[2]/ul[2]/li/div/div[2]/div[5]/a[1]'
GET_NOTIFIED_TWO_BR_XPATH = '/html/body/div/div/section/section/div[2]/ul[3]/li/div/div[2]/div[5]/a[1]'


def create_check_file(file):
    """Write file; quick hack to not send sms again until we delete this file"""
    with open(file, 'w+') as f:
        f.write('delete me to continue checking!')


def get_generic_exc_count():
    """Returns generic exception count"""
    try:
        with open(GENERIC_COUNT) as f:
            return json.load(f).get('count')
    except FileNotFoundError:
        with open(GENERIC_COUNT, 'w') as f:
            json.dump({'count': 0}, f)
        return 0


def update_generic_exc_count():
    """Updates generic exception count"""
    current_count = get_generic_exc_count()
    current_count += 1
    with open(GENERIC_COUNT, 'w') as f:
        json.dump({'count': current_count}, f)


def text_via_twilio(msg):
    """Text the numbers via twilio"""
    client = twilio_rest.Client(TWILIO_ACCOUNT, TWILIO_TOKEN)
    client.messages.create(
        to=f'+{MY_NUMBER}',
        from_=f'+{TWILIO_FROM_NUMBER}',
        body=msg
    )
    client.messages.create(
        to=f'+{ALT_MY_NUMBER}',
        from_=f'+{TWILIO_FROM_NUMBER}',
        body=msg
    )


def check_1_br(driver):
    """Check 1 bedroom availability

    :param webdriver.Firefox driver: selenium webdriver
    """
    try:
        one_bed = driver.find_element_by_xpath(ONE_BED_XPATH)
        one_bed.click()
        get_notified_element = driver.find_element_by_xpath(
            GET_NOTIFIED_ONE_BR_XPATH
        )
        time.sleep(5)
    except Exception:
        msg = f'Failed to find GET NOTIFIED ELEMENT for 1 bedroom! go to {URL}'
        print(msg)
        text_via_twilio(msg)
        create_check_file(CHECK_ONE)
        return

    if 'get notified' not in get_notified_element.text.lower():
        msg = f'get notified not in element for 1 bedroom! go to {URL}'
        print(msg)
        text_via_twilio(msg)
        create_check_file(CHECK_ONE)
        return


def check_2_br(driver):
    """Check 2 bedroom availability

    :param webdriver.Firefox driver: selenium driver
    """
    try:
        two_bed = driver.find_element_by_xpath(TWO_BED_XPATH)
        two_bed.click()
        get_notified_element = driver.find_element_by_xpath(
            GET_NOTIFIED_TWO_BR_XPATH
        )
        time.sleep(5)
    except Exception:
        msg = f'Failed to find GET NOTIFIED ELEMENT for 2 bedroom! go to {URL}'
        print(msg)
        text_via_twilio(msg)
        create_check_file(CHECK_TWO)
        return

    if 'get notified' not in get_notified_element.text.lower():
        msg = f'get notified not in element for 2 bedroom! go to {URL}'
        print(msg)
        text_via_twilio(msg)
        create_check_file(CHECK_TWO)
        return


def check_availability():
    """Launch geckodriver and check availability"""
    options = webdriver.FirefoxOptions()
    options.headless = True
    options.add_argument("--headless")
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")
    driver = webdriver.Firefox(
        options=options,
        executable_path=r'/usr/local/bin/geckodriver'
    )
    driver.set_page_load_timeout(15)
    driver.get(URL)
    print(f'Page Title: {driver.title}')
    if not os.path.exists(CHECK_ONE):
        check_1_br(driver)
    else:
        print(f'Already checked! delete {CHECK_ONE} to check again')

    if not os.path.exists(CHECK_TWO):
        check_2_br(driver)
    else:
        print(f'Already checked! delete {CHECK_TWO} to check again')
    driver.close()


def is_connected():
    """Check if we have internet access"""
    choice = random.choice(['https://google.com', 'https://bing.com'])
    try:
        requests.get(choice, timeout=10.0)
        return True
    except requests.exceptions.RequestException:
        print('No internet connection?')
        return False


if __name__ == '__main__':
    required_vars = [TWILIO_ACCOUNT,
                     TWILIO_TOKEN,
                     TWILIO_FROM_NUMBER,
                     MY_NUMBER,
                     ALT_MY_NUMBER]
    if not all(required_vars):
        print('Missing required env vars!')
        raise ValueError('Missing required env vars!')

    if not is_connected():
        # no internet possibly, exit with 1
        exit(1)

    try:
        print(f'checking availability {datetime.datetime.utcnow().isoformat()}...')
        check_availability()
    except Exception as e:
        print(str(e))
        curr_count = get_generic_exc_count()
        if curr_count < 3:
            print(f'{curr_count} generic exceptions have occurred, alerting!')
            update_generic_exc_count()
            text_via_twilio(str(e)[0:500])
        else:
            print(
                f'{curr_count}+ generic exceptions have occurred. delete '
                f'{GENERIC_COUNT} to receive alerts again.'
            )
