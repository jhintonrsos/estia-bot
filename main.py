"""Bot to check for estia availability"""
import logging
import os
import time

import selenium.webdriver as webdriver
import twilio.rest as twilio_rest

logging.basicConfig()
_logger = logging.getLogger(__file__)
_logger.setLevel(logging.INFO)

TWILIO_ACCOUNT = os.environ.get('TWILIO_ACCOUNT')
TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER')
MY_NUMBER = os.environ.get('MY_NUMBER')
ALT_MY_NUMBER = os.environ.get('ALT_MY_NUMBER')

# if this file is present, it means a twilio msg was sent.
# delete to let the script run again. This avoids spamming until we verify
# and acknowledge the notification by deleting the file
CHECK_ONE = 'check_one.log'
CHECK_TWO = 'check_two.log'

URL = 'https://estiaatlakewoodranch.prospectportal.com/bradenton/estia-at-lakewood-ranch/conventional/'
ONE_BED_XPATH = '/html/body/div[1]/div/section/section/div[2]/ul[1]/li[1]/a/span[1]'
TWO_BED_XPATH = '/html/body/div[1]/div/section/section/div[2]/ul[1]/li[2]/a/span[1]'
GET_NOTIFIED_ONE_BR_XPATH = '/html/body/div/div/section/section/div[2]/ul[2]/li/div/div[2]/div[5]/a[1]'
GET_NOTIFIED_TWO_BR_XPATH = '/html/body/div/div/section/section/div[2]/ul[3]/li/div/div[2]/div[5]/a[1]'


def create_check_file(file):
    """Write file; quick hack to not send sms again until we delete this file"""
    with open(file, 'w+') as f:
        f.write('delete me to continue checking!')


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
        _logger.exception(msg)
        text_via_twilio(msg)
        create_check_file(CHECK_ONE)
        return

    if 'get notified' not in get_notified_element.text.lower():
        msg = f'get notified not in element for 1 bedroom! go to {URL}'
        _logger.warning(msg)
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
        _logger.exception(msg)
        text_via_twilio(msg)
        create_check_file(CHECK_TWO)
        return

    if 'get notified' not in get_notified_element.text.lower():
        msg = f'get notified not in element for 2 bedroom! go to {URL}'
        _logger.warning(msg)
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
    driver.get(URL)
    _logger.info(f'Page Title: {driver.title}')
    if not os.path.exists(CHECK_ONE):
        check_1_br(driver)
    else:
        _logger.info(f'Already checked! delete {CHECK_ONE} to check again')

    if not os.path.exists(CHECK_TWO):
        check_2_br(driver)
    else:
        _logger.info(f'Already checked! delete {CHECK_TWO} to check again')
    driver.close()


if __name__ == '__main__':
    required_vars = [TWILIO_ACCOUNT,
                     TWILIO_TOKEN,
                     TWILIO_FROM_NUMBER,
                     MY_NUMBER,
                     ALT_MY_NUMBER]
    if not all(required_vars):
        raise ValueError('Missing required env vars!')
    check_availability()
