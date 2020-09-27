from typing import Optional, Union

import yaml
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

from .utils import Location, Session


class Booker:

    def __init__(self,
                 location: Location,
                 session: Session,
                 config_path: str = 'config.yml',
                 options: Optional[Options] = None) -> None:

        self.location: Location = location
        self.session: Session = session
        self.config_path: str = config_path
        self.options: Options = options if options is not None else self.set_options()

        self.browser: Union[WebDriver, None] = None

    def __del__(self):

        if self.browser:
            self.browser.quit()

    @staticmethod
    def set_options() -> Options:

        chrome_option = Options()
        chrome_option.headless = True

        return chrome_option

    def set_browser(self) -> None:
        self.browser = webdriver.Chrome(ChromeDriverManager().install(), options=self.options)

    def load_config(self) -> dict:

        try:
            with open(self.config_path) as fconfig:
                config = yaml.load(fconfig, Loader=yaml.FullLoader)
        except FileNotFoundError as e:
            raise e

        return config

    def book(self) -> None:

        booking_url: str = 'https://www.library.manchester.ac.uk/locations-and-opening-hours/study-spaces/booking/'

        session_xpath: str = f'//*[@id="content"]/div/section/article/div[{self.location}]/table/tbody/tr[{self.session}]/td[4]/a'
        confirm_xpath: str = '//*[@id="content"]/div/section/article/a'
        register_xpath: str = '//*[@id="register"]/div[5]/input'

        # start browser instance
        if not self.browser:
            self.set_browser()

        # load user config
        user_config = self.load_config()

        # navigate to webpage
        self.browser.get(booking_url)
        self.browser.find_element_by_xpath(session_xpath).click()
        self.browser.find_element_by_xpath(confirm_xpath).click()

        # submit form
        try:
            self.browser.find_element_by_id('username').send_keys(user_config['username'])
            self.browser.find_element_by_id('password').send_keys(user_config['password'])
        except KeyError as e:
            raise e

        self.browser.find_element_by_name('submit').click()
        self.browser.find_element_by_xpath(register_xpath).click()

        self.browser.quit()
