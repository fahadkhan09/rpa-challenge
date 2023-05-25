import re
from pathlib import Path
from pprint import pprint
from datetime import datetime
from calendar import monthrange
from typing import Optional, Tuple
from dateutil.relativedelta import relativedelta

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from RPA.HTTP import HTTP
from RPA.Excel.Files import Files
from RPA.Browser.Selenium import Selenium


class News:
    def __init__(self, search_phrase: str, months: int, sections: Optional[list] = None):
        """

        :param search_phrase: A phrase to search news related to it.
        :param months: numbers of months which are included
        :param sections: section/categories to select the news
        """
        self.search_phrase = search_phrase
        self.sections = sections
        self.months = months

        self.driver = Selenium()

        self.lib = Files()
        self.http = HTTP()

        self.site_url = 'https://www.nytimes.com/'
        self.images_folder = Path(Path.cwd(), 'output/images')
        self.news_sheet_path = Path(Path.cwd(), "output/news.xlsx")

        self.current_date = datetime.now()
        _, self.last_day_of_current_month = monthrange(self.current_date.year, self.current_date.month)

        self.headers = ["title", "date", "description", "picture filename", "count of phrases", "contains_money"]
        self.data = []

    @staticmethod
    def change_date_format(dates: Tuple[datetime, datetime]) -> list:
        """

        :param dates: a tuple having datetime objects.
        :return: A list containing a string date.
        """
        return [arg_date.strftime('%m/%d/%Y') for arg_date in dates]

    def open_site_in_chrome(self):
        """
        Open the site in the chrome.
        :return:
        """
        pprint("Opening the NewYork Times Site.")
        self.driver.open_chrome_browser(self.site_url, maximized=True)

    def search_the_phrase(self):
        """
        Search the required word.
        :return:
        """
        pprint("Searching the search phrase.")
        self.driver.click_button_when_visible('//button[@data-test-id="search-button"]')
        self.driver.input_text(locator='//input[@name="query"]', text=self.search_phrase)
        self.driver.click_button_when_visible('//button[text()="Go"]')

    def select_sections(self):
        """
        Select section/categories of news.
        :return:
        """
        pprint("Selecting the news sections.")
        self.driver.click_element_when_visible('//button[contains(@data-testid,"multiselect")][1]')
        if self.sections:
            [self.driver.click_element_when_visible(f"//input[contains(@value, '{section.capitalize()}')]") for section
             in self.sections]

    def select_newest(self):
        """
        Select the newest news.
        :return:
        """
        pprint("Selecting the newest news.")
        self.driver.select_from_list_by_value('//select[@class="css-v7it2b"]', 'newest')

    def select_date(self):
        """
        Get the months has an integer and based on that figure out the months to be selected.
        :return:
        """
        pprint("Selecting the date based on the number of months.")
        if 12 >= self.months >= 0:
            if self.months in [0, 1]:
                start_date = self.current_date.replace(day=1)
                end_date = self.current_date.replace(day=self.last_day_of_current_month)
            else:
                start_date = (self.current_date - relativedelta(months=self.months - 1)).replace(day=1)
                end_date = self.current_date.replace(day=self.last_day_of_current_month)

            self.driver.click_button_when_visible('//button[contains(@data-testid,"search-date")]')
            self.driver.click_button_when_visible('//button[text()="Specific Dates"]')
            start_date, end_date = self.change_date_format((start_date, end_date))
            self.driver.input_text(locator='//input[@id="startDate"]', text=start_date)
            self.driver.input_text(locator='//input[@id="endDate"]', text=end_date)
            self.driver.press_key(locator='//input[@id="endDate"]', key='\ue007')
        else:
            pprint(f"{self.months} has to be in range 1-12.")

    def handle_cookie_pop_up(self):
        pprint("Handle the cookie pop-up.")
        try:
            self.driver.wait_until_page_contains_element(locator="//button[@class='css-1qw5f1g']")
            self.driver.click_element(locator="//button[@class='css-1qw5f1g']")
        except AssertionError:
            pass

    def process_search_results(self):
        """
        Fetched all the listed news with their date, title, description, image, count of search phrase, bool based
        on the money check.
        :return:
        """

        pprint("Fetching all the news search result based on the parameters.")
        self.handle_cookie_pop_up()

        show_more_button_check = True
        while show_more_button_check:
            try:
                if not self.driver.does_page_contain_button("//button[text()='Show More']"):
                    break
                show_more = self.driver.find_element("//button[text()='Show More']")
                actions = ActionChains(self.driver.driver)
                actions.move_to_element(show_more).perform()
                show_more.click()
            except (NoSuchElementException, StaleElementReferenceException):
                pass

        results_rows = self.driver.find_elements(
            '//ol[@data-testid="search-results"]//li[@data-testid="search-bodega-result"]')

        titles, descriptions, dates, img_paths, search_counts, contains_money = list(), list(), list(), list(), list(), list()
        for row in results_rows:
            title = row.find_element(By.CLASS_NAME, "css-2fgx4k").text
            if title not in titles:
                titles.append(title)
                description = row.find_element(By.CLASS_NAME, "css-16nhkrn").text
                descriptions.append(description)
                dates.append(row.find_element(By.CLASS_NAME, "css-17ubb9w").text)
                img_paths.append(self.download_image(row.find_element(By.CLASS_NAME, "css-rq4mmj"), title))
                title_and_description = f'{title} {description}'
                search_counts.append(title_and_description.count(self.search_phrase))
                contains_money.append(bool(
                    re.match(r'(?:\$\d+\,?\.?\d+|\d+\s*(?:usd|dollars))', title_and_description, re.IGNORECASE)))
        else:
            self.data = [titles, descriptions, dates, img_paths, search_counts, contains_money]
            pprint("Data Fetched successfully.")

    def download_image(self, picture_elem, pic_name: str):
        """

        :param picture_elem: WebElement of the selected picture.
        :param pic_name: News title which has to be the name of picture.
        :return: picture name if picture is downloaded successfully else None.
        """
        image_name = str(Path(self.images_folder, pic_name))
        response = self.http.download(picture_elem.get_attribute("src"),
                                      target_file=image_name)
        return image_name if response.__dict__.get('status_code') == 200 else None

    def create_excel_sheet(self):
        """
        Create an Excel sheet.
        :return:
        """
        pprint("Creating News data excel sheet.")
        self.lib.create_workbook(path=str(self.news_sheet_path), sheet_name='news sheet')
        self.lib.save_workbook()

    def append_data(self):
        """
        Populate the Excel sheet with fetched data.
        :return:
        """
        pprint("Appending data to news sheet.")
        self.lib.open_workbook(path=str(self.news_sheet_path))
        self.lib.append_rows_to_worksheet(dict(zip(self.headers, self.data)), header=True)
        self.lib.save_workbook()

    def release_resources(self):
        """
        Close the Selenium browser.
        :return:
        """
        pprint("Releasing the resources.")
        self.driver.close_browser()
