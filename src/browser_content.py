from selenium.webdriver.support.select import By
from elasticsearch import Elasticsearch
import configparser
import threading


url = "https://www.dragonsteel.com.tw/"
config = configparser.ConfigParser()
config.read('es_credentials.ini', encoding='utf-8')
dictionary = {}


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
        return self.title

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
        ## 取得該網站的html有幾個heading tag（h1. h2, h3....）##
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
    Singleton Class. Only one instance will be created. 
    """
    __elastic_con = None
    __es_lock = threading.Lock()
    __map = None

    @staticmethod
    def get_instance(map):
        if ElasticClient.__elastic_con is None:
            with ElasticClient.__es_lock:
                ElasticClient.__elastic_con = Elasticsearch(cloud_id=config['ELASTIC']['cloud_id'],
                                                            http_auth=(config['ELASTIC']['user'], config['ELASTIC']['password']))
                ElasticClient.__map = map
        return ElasticClient.__elastic_con

    def __init__(self):
        raise Exception("This class is Singleton. Use get_instance()")

    def __create_index(self, index_name):
        self.elastic_con.indices.create(
            index=index_name, ignore=400, body=self.map_body)
