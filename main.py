from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.select import By
from selenium.webdriver.support.ui import WebDriverWait


url = "https://www.dragonsteel.com.tw/"

def detect_changes():
    # initialization #
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    wait = WebDriverWait(browser, 10)
    browser.get(url)
    l = browser.find_elements(by=By.XPATH, value='//li/a')
    for a in l:
        print(a.get_attribute('href'))


detect_changes()


class BrowserContent:
    def __init__(self, browser, url: str):
        self.browser = browser
        self.url = url

    def __getattr__(self, method):
        getattr(self.browser, method) 
        # raise AttributeError

    def list_whole_html(self):
        page = self.execute_script("return new XMLSerializer().serializeToString(document)") 
        return page

    def list_title(self):
        return self.title

    def list_ids(self):
        for id in self.find_elements(by=By.XPATH, value='//*[@id]'):
            yield id.get_attribute('id')

    def list_classes(self):
        for cls in self.find_elements(by=By.XPATH, value='//*[@class]'):
            yield cls.get_attribute('class')
    
    def list_hyperlinks(self):
        for link in self.find_elements(by=By.XPATH, value='//li/a'):
            yield link.get_attribute('href')
    

        
