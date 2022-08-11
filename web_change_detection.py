import browser_content
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


options = Options()
options.headless = True
browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
new = browser_content.BrowserContent(browser=browser, url='https://www.dragonsteel.com.tw/')
new.browser_init()
print(new.list_ids().next())