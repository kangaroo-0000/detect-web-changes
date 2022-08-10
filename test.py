import main
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.select import By
from selenium.webdriver.support.ui import WebDriverWait

new = main.BrowserContent(browser=webdriver.Chrome(service=Service(ChromeDriverManager().install())), url='https://www.dragonsteel.com.tw/')
print(new.list_ids())