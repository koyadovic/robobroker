from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import DesiredCapabilities
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException


def get_current_browser_driver(headless=False):
    opt = webdriver.ChromeOptions()
    if headless:
        opt.add_argument("--headless")
    opt.add_argument('user-data-dir=/home/user/.config/google-chrome/Default')
    driver = webdriver.Chrome(options=opt)
    driver.implicitly_wait(10)
    driver.set_page_load_timeout(20)
    return driver


