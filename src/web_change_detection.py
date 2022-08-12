import browser_content
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import click
import os
import json
import ast

map = {
    "mappings": {
        "properties": {
            "whole-html": {"type": "text"},
            "title": {
                "type": "keyword"
            },
            "meta_content": {
                "type": "text"
            },
            "id": {
                "type": "text"
            },
            "class": {
                "type": "text"
            },
            "hyperlink": {
                "type": "keyword"
            },
            "heading-tag": {
                "type": "text"
            },
            "paragraph-tag": {
                "type": "text"
            }
        }
    }
}

build_dir = "../web_result/"


@click.command()
@click.option('-s', '--save2db', is_flag=True, help='輸入網站URL，並存取該網站HTML到本地資料夾')
@click.option('-c', '--compare2db', is_flag=True, help='輸入網站URL，並與對應資料比對該網站HTML有無更新')
@click.argument('urls', nargs=-1)
def check(save2db, compare2db, urls):
    for url in urls:
        if save2db:
            with open(os.path.join(build_dir, f'{url.replace("/", "")}.txt'), 'w+', encoding='utf-8') as f:
                json.dump(combo(url), f, ensure_ascii=False)
        if compare2db:
            if os.path.exists(os.path.join(build_dir, f'{url.replace("/", ".")}.txt')):
                with open(os.path.join(build_dir, f'{url.replace("/", ".")}.txt'), 'w', encoding='utf-8') as f:
                    dict1 = ast.literal_eval(f.read())
                    dict2 = combo(url)
                    value = {k: dict2[k] for k in set(dict2) - set(dict1)}
            else:
                raise FileNotFoundError


def write2db():
    es = browser_content.ElasticClient.get_instance(map)
    es.indices.create(index='web-change', ignore=400, body=map)
    es.index(index='test', body=combo('https://www.dragonsteel.com.tw/'))
    print(es.count(index='test'))


def combo(url: str):
    dict = {}
    options = Options()
    options.headless = True
    browser = webdriver.Chrome(service=Service(
        ChromeDriverManager().install()), options=options)
    new = browser_content.BrowserContent(
        browser=browser, url=url)
    new.browser_init()
    dict['whole-html'] = new.list_whole_html()
    dict['title'] = new.list_title()
    dict['meta-content'] = list(new.list_meta_contents())
    dict['class'] = list(new.list_classes())
    dict['id'] = list(new.list_ids())
    dict['heading-tag'] = list(new.list_heading_tags())
    dict['paragraph-tag'] = list(new.list_paragraph_tags())
    dict['hyperlink'] = list(new.list_hyperlinks())
    return dict


if __name__ == '__main__':
    check()
