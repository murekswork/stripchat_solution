import logging
import threading
import time

from django.conf import settings
from playwright.sync_api import sync_playwright, Page, Frame, ElementHandle
from twocaptcha import TwoCaptcha

from accounts.models import StripChatUser


class ParserService:

    def __init__(self, pw):
        self.logger = logging.getLogger("ParserService")
        self.playwright = pw
        self.page: Page
        self.captcha_link: str | None = None

    def create_browser(self) -> Page:
        browser = self.playwright.webkit.launch(headless=False)
        context = browser.new_context(**self.playwright.devices["iPhone 6"])
        page = context.new_page()
        self.page = page
        page.goto("https://stripchat.global/login")
        self.logger.debug("CREATED BROWSER")
        return page

    def get_captcha_content_frame(self, page: Page) -> Frame:
        self.logger.debug("GOT CAPTCHA CONTENT FRAME")
        captcha_frame_selector = page.wait_for_selector("iframe[src*='recaptcha/api2']")
        self.set_captcha_link(captcha_frame_selector)
        captcha_frame_content = captcha_frame_selector.content_frame()
        return captcha_frame_content

    def set_captcha_link(self, captcha_frame: ElementHandle):
        self.logger.debug("SET CAPTCHA LINK")
        self.captcha_link = captcha_frame.get_attribute("src")

    def click_robot_checkbox(self, captcha_frame: Frame):
        self.logger.debug("CLICKED ROBOT CHECKBOX")
        robot_checkbox = captcha_frame.wait_for_selector("#recaptcha-anchor")
        robot_checkbox.click()

    def get_captcha_site_key(self):
        self.logger.debug("GETTING CAPTCHA SITE KEY")
        if self.captcha_link:
            site_key = self.captcha_link.split("k=")[1].split("&")[0]
        else:
            raise ValueError("Could not parse captcha link!")
        return site_key

    def input_account_credentials(self, username: str, password: str):
        self.logger.debug("START TO INPUT ACCOUNT CREDENTIALS")
        username = username
        password = password
        self.page.wait_for_selector("input[id='login_login_or_email']").fill(username)
        self.page.wait_for_selector("input[id='login_password']").fill(password)

    def input_captcha_code(self, captcha_frame: Frame, code: str):
        self.logger.debug("START TO INPUT CAPTCHA CODE")
        captcha_input = self.page.locator("#g-recaptcha-response")
        print("Got captcha hidden response")
        captcha_input.evaluate(f'(element) => {{ element.value = "{code}"; }}')

    def call_callback(self, captcha_frame: Frame, captcha_code: str):
        self.logger.debug("CALLING CAPTCHA CALLBACK")
        letters = "QWERTYUIOPASDFGHJKLZXCVBNM"
        for letter in letters:
            try:
                resp = self.page.evaluate(
                    f"___grecaptcha_cfg.clients['0']['{letter}']['{letter}']"
                )
                if "callback" in resp:
                    self.page.evaluate(
                        "___grecaptcha_cfg.clients['0']['{}']['{}']['callback']('{}')".format(
                            letter, letter, captcha_code
                        )
                    )
                    break
            except Exception as e:
                self.logger.debug(f'{e} Could not find callback method for letter: {letter}')
                continue

    def login(self):
        self.logger.debug("TRYING TO LOG IN")
        try:
            self.page.get_by_role("button", name="Log In").click()
            self.logger.debug("LOGGED IN SUCCESSFULLY")
        except Exception as e:
            self.logger.debug("LOGGED IN SUCCESSFULLY")
            self.page.get_by_role("button", name="Войти").click()

    def search(self, username: str):
        self.page.get_by_placeholder("Search models, tags or").fill("{}".format(username))
        self.page.get_by_placeholder("Search models, tags or").press("Enter")
        self.logger.debug("SEARCHING FOR REQUESTED USERNAME")
        time.sleep(30)


class CaptchaSolver:

    def __init__(self, site_key: str, api_key: settings.CAPTCHA_SOLVER_API_KEY):
        self.solver = TwoCaptcha(apiKey=api_key)
        self.site_key = site_key

    def solve_captcha(self) -> str:
        captcha_code = self.solver.recaptcha(
            version="v2", sitekey=self.site_key, url="https://stripchat.global/login"
        )
        logging.warning("GOT CAPTCHA CODE RESPONSE!")
        return captcha_code["code"]


def run_in_thread(user: StripChatUser, search_username: str):
    thread = threading.Thread(
        target=solve_captcha_and_login,
        args=(
            user,
            search_username,
        ),
        daemon=True,
    )
    thread.start()
    return


def solve_captcha_and_login(user: StripChatUser, search_username: str):
    with sync_playwright() as pw:
        parser = ParserService(pw)
        page = parser.create_browser()
        captcha_frame = parser.get_captcha_content_frame(page)
        site_key = parser.get_captcha_site_key()

        solver = CaptchaSolver(
            site_key=site_key, api_key=settings.CAPTCHA_SOLVER_API_KEY
        )
        captcha_code = solver.solve_captcha()

        parser.input_captcha_code(captcha_frame, captcha_code)
        parser.input_account_credentials(user.username, password=user.password)
        parser.call_callback(captcha_frame, captcha_code)

        parser.login()

        parser.search(search_username)
