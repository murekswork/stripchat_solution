import logging
import threading
import time

from accounts.models import StripChatUser
from django.conf import settings
from logging_.decorators import log_exception
from playwright.sync_api import sync_playwright, Page, Frame, ElementHandle
from twocaptcha import TwoCaptcha

parsing_logger = logging.getLogger(name="StripChatService logger")
captcha_logger = logging.getLogger(name="CaptchaSolver logger")


class StripChatLoggingService:
    def __init__(self, pw):
        self.playwright = pw
        self.page: Page
        self.captcha_link: str

    @log_exception(parsing_logger)
    def get_browser_page(self) -> Page:
        """Method to create a browser and the page"""
        browser = self.playwright.webkit.launch(headless=False)
        context = browser.new_context(**self.playwright.devices["iPhone 6"])
        page = context.new_page()
        self.page = page
        page.goto("https://stripchat.global/login")
        return page

    @log_exception(parsing_logger)
    def get_captcha_content_frame(self) -> Frame:
        """Method to select captcha content frame and return it"""
        captcha_frame_selector = self.page.wait_for_selector(
            "iframe[src*='recaptcha/api2']"
        )
        self.set_captcha_link(captcha_frame_selector)
        captcha_frame_content = captcha_frame_selector.content_frame()
        return captcha_frame_content

    @log_exception(parsing_logger)
    def set_captcha_link(self, captcha_frame: ElementHandle) -> None:
        self.captcha_link = captcha_frame.get_attribute("src")

    @log_exception(parsing_logger)
    def get_captcha_site_key(self) -> str:
        site_key = self.captcha_link.split("k=")[1].split("&")[0]
        return site_key

    @log_exception(parsing_logger)
    def input_account_credentials(self, username: str, password: str) -> None:
        """Method to enter provided uname and pass to login inputs"""
        username = username
        password = password
        self.page.wait_for_selector("input[id='login_login_or_email']").fill(username)
        self.page.wait_for_selector("input[id='login_password']").fill(password)

    @log_exception(parsing_logger)
    def input_captcha_code(self, code: str) -> None:
        """Method to enter provided captcha code into hidden captcha response input"""
        captcha_input = self.page.locator("#g-recaptcha-response")
        captcha_input.evaluate(f'(element) => {{ element.value = "{code}"; }}')

    def call_captcha_callback(self, captcha_code: str) -> None:
        """Method to iterate over all site's clients and try to call 'callback' method"""
        letters = "XQWERTYUIOPASDFGHJKLZCVBNM"
        for letter in letters:
            try:
                resp = self.page.evaluate(
                    "___grecaptcha_cfg.clients['0']['{}']['{}']".format(letter, letter)
                )
                if "callback" in resp:
                    self.page.evaluate(
                        "___grecaptcha_cfg.clients['0']['{}']['{}']['callback']('{}')".format(
                            letter, letter, captcha_code
                        )
                    )
                    break
            except Exception as e:
                continue

    @log_exception(parsing_logger)
    def login(self) -> None:
        login_button = self.page.wait_for_selector(
            ".btn.btn-inline-block.btn-login-alternative.btn-medium.login-form__submit"
        )
        login_button.click()
        time.sleep(5)

    @log_exception(parsing_logger)
    def search(self, username: str) -> None:
        """Method to enter required string in site's search field and click search button """
        search_button = self.page.get_by_role("search").click()
        try:
            search_window = self.page.get_by_placeholder(
                "Search models, tags or countries, tip menu"
            )
        except:
            search_window = self.page.get_by_placeholder(
                "Поиск по моделям, категориям, странам и меню чаевых"
            )
        search_window.fill(username)
        search_window.press("Enter")


class CaptchaSolver:

    def __init__(self, site_key: str, api_key: settings.CAPTCHA_SOLVER_API_KEY):
        self.solver = TwoCaptcha(apiKey=api_key)
        self.site_key = site_key

    @log_exception(captcha_logger)
    def solve_captcha(self) -> str:
        """Method to send site's key and url to captcha solving service"""
        captcha_code = self.solver.recaptcha(
            version="v2", sitekey=self.site_key, url="https://stripchat.global/login"
        )
        return captcha_code["code"]


def run_in_thread(user: StripChatUser, search_username: str):
    """Function to call main function in separate thread with daemon mode"""
    thread = threading.Thread(
        target=solve_captcha_and_login,
        args=(
            user,
            search_username,
        ),
        daemon=True,
    )
    thread.start()


def solve_captcha_and_login(
        user: StripChatUser, search_username: str, retries: int = 0
):
    """
    This function attempts to solve a captcha, login to a StripChat account,
     and search for a specified username. If attempt fails,
     it retries up to 5 times (by default).
     The function takes a StripChat user object, a search username,
     and an optional number of retries as parameters.
    """
    try:
        with sync_playwright() as pw:
            parser = StripChatLoggingService(pw)
            parser.get_browser_page()
            captcha_frame = parser.get_captcha_content_frame()
            site_key = parser.get_captcha_site_key()

            solver = CaptchaSolver(site_key, settings.CAPTCHA_SOLVER_API_KEY)
            captcha_code = solver.solve_captcha()

            parser.input_captcha_code(captcha_code)
            parser.input_account_credentials(user.username, user.password)
            parser.call_captcha_callback(captcha_code)

            parser.login()

            parser.search(search_username)
            logging.debug("Solving captcha and login completed!")
            time.sleep(20)
    except Exception:
        if retries < 5:
            logging.warning(
                "Could not solve captcha and login for {} and {}, retrying ({} / 5)!".format(
                    user, search_username, retries
                )
            )
            solve_captcha_and_login(user, search_username, retries + 1)
        else:
            logging.error("Could not solve captcha and reached max retries limit!")
