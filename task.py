"""Template robot with Python."""
import os
from pprint import pprint
from RPA.Robocorp.WorkItems import WorkItems

from news import News


def get_data_for_the_process():
    """
    Get WorkItems if running in robocorp else get the local data.
    :return: A dict contains required data for automation
    """
    pprint("Getting Data.")
    if os.environ.get("RC_PROCESS_ID"):
        work_items = WorkItems()
        work_items.get_input_work_item()
        data = work_items.get_work_item_variables()
    else:
        data = {"search_phrase": "Artificial Intelligence", "months": 3,
                "sections": ["arts", "books", "opinion"]}
    pprint(data)
    return data


class Task:
    """
    A Task class contains the steps for the News automation.
    """

    def __init__(self, data):
        """

        :param data: A dict.
        """
        self.news = News(**data)

    def start_the_task(self):
        """
        Perform the news functional steps.
        :return:
        """
        pprint("Task started.")
        self.news.open_site_in_chrome()
        self.news.search_the_phrase()
        self.news.select_sections()
        self.news.select_newest()
        self.news.select_date()
        self.news.process_search_results()
        self.news.create_excel_sheet()
        self.news.append_data()

    def end_the_task(self):
        """
        Release the resources that are currently in use.
        :return:
        """
        self.news.release_resources()
        pprint("Task ended.")


if __name__ == "__main__":
    task = Task(get_data_for_the_process())
    try:
        task.start_the_task()
    except Exception as e:
        print(e)
    finally:
        task.end_the_task()
