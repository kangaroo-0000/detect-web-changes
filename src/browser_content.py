from selenium.webdriver.support.select import By
from opensearchpy import OpenSearch, RequestsHttpConnection
import configparser
import threading
import hashlib
from abc import ABC, abstractmethod
import typing
from base64 import b64decode
import os
import json


config = configparser.ConfigParser()
config.read('es_credentials.ini', encoding='utf-8')


class BrowserContent:
    def __init__(self, browser, url: str):
        self.browser = browser
        self.url = url

    def browser_init(self):
        self.get(self.url)

    def __getattr__(self, method):
        return getattr(self.browser, method)
        # raise AttributeError

    def list_whole_html(self):
        page = self.execute_script(
            "return new XMLSerializer().serializeToString(document)")
        return page

    def list_title(self):
        return self.title.split(" ")

    def list_ids(self):
        for id in self.find_elements(by=By.XPATH, value='//*[@id]'):
            yield id.get_attribute('id')

    def list_classes(self):
        for cls in self.find_elements(by=By.XPATH, value='//*[@class]'):
            yield cls.get_attribute('class')

    def list_meta_contents(self):
        for name in self.find_elements(by=By.XPATH, value='//*[@name]'):
            name = name.get_attribute('name')
            try:
                yield self.find_element(
                    by=By.XPATH, value=f'//meta[@name="{name}"]').get_attribute('content')
            except:
                continue

    def list_hyperlinks(self):
        for link in self.find_elements(by=By.XPATH, value='//li/a'):
            yield link.get_attribute('href')

    # def print_the_page_down_as_pdf(self):
    #     pdf = b64decode(self.print_page())
    #     with open('new.pdf', 'wb') as f:
    #         f.write(pdf)

    def list_heading_tags(self):
        h_tag_count = 1
        ## 取得該網站的html有幾個heading tag（h1, h2, h3..., h6）##
        while h_tag_count <= 6:
            try:
                self.find_elements(by=By.TAG_NAME, value=f'h{h_tag_count}')
            except:
                break
            else:
                h_tag_count = h_tag_count + 1

        for count in range(1, h_tag_count+1):
            for h_tags in self.find_elements(by=By.TAG_NAME, value=f'h{count}'):
                yield h_tags.get_attribute('textContent')

    def list_paragraph_tags(self):
        for p_tags in self.find_elements(by=By.XPATH, value='//p'):
            yield p_tags.get_attribute('textContent')

    def browser_close(self):
        self.close()


class ElasticClient:
    """
    A rough implementation of a Singleton Class. Only one instance will be created throughout runtime.
    """
    __elastic_con = None
    __es_lock = threading.Lock()

    @staticmethod
    def get_instance():
        if ElasticClient.__elastic_con is None:
            with ElasticClient.__es_lock:
                ElasticClient.__elastic_con = OpenSearch(hosts=[{'host': '10.11.233.105', 'port': 9200}],
                                                         http_auth=(
                                                             config['ELASTIC']['user'], config['ELASTIC']['password']),
                                                         use_ssl=True,
                                                         verify_certs=False,
                                                         ssl_assert_hostname=False,
                                                         ssl_show_warn=False,
                                                         connection_class=RequestsHttpConnection)
        return ElasticClient.__elastic_con

    def __init__(self):
        raise Exception("This class is Singleton. Use get_instance()")


class Saver(ABC):
    @ abstractmethod
    def __init__(self, path: str, filename: str, browser_content: typing.Type[BrowserContent]):
        self.browser_content = browser_content
        self.path = path
        self.filename = filename
        self.browser_content.browser_init()

    def save():
        pass


class SaveAsPDF(Saver):
    def __init__(self, path: str, filename: str, browser_content: typing.Type[BrowserContent]):
        super().__init__(path, filename, browser_content)

    def save(self) -> typing.BinaryIO:
        pdf = b64decode(self.browser_content.print_page())
        with open(os.path.join(self.path, self.filename), 'wb') as f:
            f.write(pdf)
            return f


class SaveTagsAsPlainText(Saver):
    def __init__(self, path: str, filename: str, browser_content: typing.Type[BrowserContent]):
        super().__init__(path, filename, browser_content)

    def get_text_2b_saved(self) -> typing.Dict:
        dict = {}
        dict['title'] = list(self.browser_content.list_title())
        dict['meta-content'] = list(self.browser_content.list_meta_contents())
        dict['class'] = list(self.browser_content.list_classes())
        dict['id'] = list(self.browser_content.list_ids())
        dict['heading-tag'] = list(self.browser_content.list_heading_tags())
        dict['paragraph-tag'] = list(
            self.browser_content.list_paragraph_tags())
        dict['hyperlink'] = list(self.browser_content.list_hyperlinks())
        return dict

    def save(self) -> typing.IO:
        dict = self.get_text_2b_saved()
        with open(os.path.join(self.path, self.filename), 'w+', encoding='utf-8') as f:
            json.dump(dict, f, ensure_ascii=False)
            return f


class SaveHTMLAsHash(Saver):
    def __init__(self, path: str, filename: str, browser_content: typing.Type[BrowserContent]):
        super().__init__(path, filename, browser_content)

    def get_hash_2b_saved(self):
        h = hashlib.new('sha256')
        h.update(bytes(self.browser_content.list_whole_html(), 'utf-8'))
        return h

    def save(self) -> typing.IO:
        h = self.get_hash_2b_saved()
        with open(os.path.join(self.path, self.filename), 'w+', encoding='utf-8') as f:
            f.write(h.hexdigest())
            return f


class SaveHTMLAsPlainText(Saver):
    def __init__(self, path: str, filename: str, browser_content: typing.Type[BrowserContent]):
        super().__init__(path, filename, browser_content)

    def save(self) -> typing.IO:
        with open(os.path.join(self.path, self.filename), 'w+', encoding='utf-8') as f:
            f.write(self.get_html_2b_saved())
            return f

    def get_html_2b_saved(self):
        return self.browser_content.list_whole_html()
