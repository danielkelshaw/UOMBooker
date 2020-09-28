import datetime
import os
from typing import Optional, Union

import yaml
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

from .utils import Location, Session
from .utils.exceptions import AlreadyBookedError, LoginError, SessionExpiredError, UnknownBookingError


class Booker:

    def __init__(self,
                 location: Location,
                 session: Session,
                 config_path: str = 'config.yml',
                 options: Optional[Options] = None) -> None:

        """Study Space Booking Class.

        Parameters
        ----------
        location: Location
            Determines which study space to book.
        session: Session
            Determines which session to book.
        config_path: str
            Path to .yml file holding login information.
        options: Optional[Options]
            Options to use in the webdriver.
        """

        self.location: Location = location
        self.session: Session = session
        self.config_path: str = config_path
        self.options: Options = options if options is not None else self.set_options()

        self.ss_unknown_booking_error: bool = True
        self.ss_filepath: str = os.path.join(
            os.getcwd(),
            f'{datetime.datetime.now().strftime("%m%d_%H%M%S")}_browser.png'
        )

        self.browser: Union[WebDriver, None] = None

        self.today = datetime.datetime.today()
        self.weekday = self.today.weekday()

        self.am_cutoff = self.today.replace(hour=12, minute=30, second=0, microsecond=0)
        self.pm_cutoff = self.today.replace(hour=16, minute=30, second=0, microsecond=0)

        self._check_datetime()

    def __del__(self) -> None:

        """Safely quit browser on object deletion."""

        if self.browser:
            try:
                self.browser.quit()
            except ImportError:
                pass

    @staticmethod
    def set_options() -> Options:

        """Provide a set of default options."""

        chrome_option = Options()
        chrome_option.headless = True
        chrome_option.add_argument("--window-size=1920,1080")

        return chrome_option

    def set_browser(self) -> None:

        """Instantiate a browser instance with the given options."""

        self.browser = webdriver.Chrome(ChromeDriverManager().install(), options=self.options)

    def load_config(self) -> dict:

        """Load user config from .yml file."""

        if not self.config_path.endswith('.yml'):
            raise ValueError('config_path must be a .yml file.')

        try:
            with open(self.config_path) as fconfig:
                config = yaml.load(fconfig, Loader=yaml.FullLoader)
        except FileNotFoundError as e:
            raise e

        return config

    def book(self, ss_final: bool = True) -> None:

        """Responsible for running the booking process.

        Parameters
        ----------
        ss_final : bool
            Saves screenshot of final page if True.
        """

        session_idx = self._get_session_idx()

        booking_url: str = 'https://www.library.manchester.ac.uk/locations-and-opening-hours/study-spaces/booking/'
        session_xpath: str = f'//*[@id="content"]/div/section/article/div[{self.location}]/table/tbody/tr[{session_idx}]/td[4]/a'
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
        self._check_login()

        # check if event already booked
        self._check_book_state()

        # click on register button
        self.browser.find_element_by_xpath(register_xpath).click()

        # check if booked successfully
        self._check_success()

        if ss_final:
            self.screenshot()

        self.browser.quit()

    def screenshot(self) -> None:

        """Takes a screenshot and saves the file."""

        self.browser.get_screenshot_as_file(self.ss_filepath)
        print(f'Saved screenshot to: {self.ss_filepath}')

    def _check_login(self) -> None:

        """Checks if login was successful.

        Raises
        ------
        LoginError
            Raises in the event that the username / password are incorrect.
        """

        try:
            msg = self.browser.find_element_by_xpath('//div[@id="msg" and @class="errors"]')
        except NoSuchElementException:
            print('Logged in successfully.')
        else:
            raise LoginError(msg.text)

    def _check_book_state(self) -> None:

        """Checks if session has already been booked.

        Raises
        ------
        AlreadyBookedError
            Raises if the session has already been booked.
        """

        try:
            msg = self.browser.find_element_by_xpath('//*[@id="content"]/div/section/article/h3')
        except NoSuchElementException:
            pass
        else:
            if msg.text == 'You are already signed up for this event.':
                raise AlreadyBookedError(msg.text)
            if msg.text == 'Thank you, you have registered for this study space period.':
                print('Booking Successful')

    def _check_success(self) -> None:

        """Checks if booking was successful.

        Raises
        ------
        UnknownBookingError
            Raises if the page is not as expected.
        """

        try:
            msg = self.browser.find_element_by_xpath('//*[@id="content"]/div/section/article/h3')
        except NoSuchElementException:
            if self.ss_unknown_booking_error:
                self.screenshot()
            raise UnknownBookingError('Page was not as expected...')
        else:
            if msg.text == 'Thank you, you have registered for this study space period.':
                print('Booking Successful')

    def _check_datetime(self) -> None:

        """Checks if chosen session is available.

        Raises
        ------
        SessionExpiredError
            Raises if the chosen session is no longer bookable.
        """

        def morning_session(session: Session) -> bool:
            return session % 2 == 1

        def afternoon_session(session: Session) -> bool:
            return session % 2 == 0

        # check if session is not in the past
        am_session, pm_session = ((self.weekday + 1) * 2 + i for i in [-1, 0])

        if self.session < am_session:
            raise SessionExpiredError('Must book for the current day / future.')
        elif self.session > pm_session:
            return

        # session must be today - check if valid booking
        valid = False
        if morning_session(self.session):
            valid = self.today < self.am_cutoff
        elif afternoon_session(self.session):
            valid = self.today < self.pm_cutoff

        if not valid:
            raise SessionExpiredError('Selected session has already closed.')

    def _get_session_idx(self) -> int:

        """Calculates session index based on current day.

        Returns
        -------
        session_idx : int
            Adjusted session index.
        """

        if self.weekday in [5, 6] or (self.weekday == 4 and self.today > self.pm_cutoff):
            session_idx = self.session
        else:
            session_idx = self.session - 2 * (self.weekday + (self.today > self.pm_cutoff))

        if session_idx <= 0:
            raise SessionExpiredError('Selected session has already closed.')

        return session_idx

