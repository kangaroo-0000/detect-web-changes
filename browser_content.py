from selenium.webdriver.support.select import By
from base64 import b64decode

url = "https://www.dragonsteel.com.tw/"
    # 
    # a = browser.find_elements(locate_with(By.XPATH, '//*[@class]').to_left_of({By.XPATH: '//*[@class]'}))
    # for l in a:
    #     print(l.get_attribute('class'))


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
    
    def list_meta_contents(self):
        for name in self.find_elements(by=By.XPATH, value='//*[@name]'):
            name = name.get_attribute('name')
            try:
                self.find_element(by=By.XPATH, value=f'//meta[@name="{name}"]').get_attribute('content')
            except:
                continue

    def list_hyperlinks(self):
        for link in self.find_elements(by=By.XPATH, value='//li/a'):
            yield link.get_attribute('href')
    
    def print_the_page_down_as_pdf(self):
        pdf = b64decode(self.print_page())
        with open('new.pdf', 'wb') as f:
            f.write(pdf)

    def list_heading_tags(self):
        h_tag_count = 1
        ## 取得該網站的html有幾個heading tag（h1. h2, h3....）##
        while True:
            try:
                self.find_elements(by= By.TAG_NAME, value=f'h{h_tag_count}')
            except:
                break
            else:
                h_tag_count = h_tag_count + 1

        for count in range(1, h_tag_count+1):
            for h_tags in self.find_elements(by=By.TAG_NAME, value=f'h{count}'):
                yield h_tags.get_attribute('textContent')

    def list_paragraph_tags(self):
        for p_tags in self.find_elements(by=By.XPATH, value='//p'):
            yield p_tags.get_attribute('innerHTML')

    def browser_close(self):
        self.close()