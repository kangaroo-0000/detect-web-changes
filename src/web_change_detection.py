import browser_content
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from pprint import pprint
from click import command, option, argument, Option, UsageError
import typing
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


class MutuallyExclusiveOption(Option):
    """
    Restricting Click Options.
    """

    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop('mutually_exclusive', []))
        help = kwargs.get('help', '')
        if self.mutually_exclusive:
            ex_str = ', '.join(self.mutually_exclusive)
            kwargs['help'] = help + (
                ' NOTE: This argument is mutually exclusive with '
                ' arguments: [' + ex_str + '].'
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise UsageError(
                "Illegal usage: `{}` is mutually exclusive with "
                "arguments `{}`.".format(
                    self.name,
                    ', '.join(self.mutually_exclusive)
                )
            )

        return super(MutuallyExclusiveOption, self).handle_parse_result(
            ctx,
            opts,
            args
        )


@command()
@option('-s', '--save2local', is_flag=True, cls=MutuallyExclusiveOption, help='輸入網站URL，並存取該網站HTML到本地資料夾', mutually_exclusive=['compare2local', 'write2es'])
@option('-c', '--compare2local', is_flag=True, cls=MutuallyExclusiveOption, help='輸入網站URL，並與本地的對應資料比對該網站HTML有無更新', mutually_exclusive=['save2local'])
@option('-w', '--write2es', is_flag=True, cls=MutuallyExclusiveOption, help='將比對不同之處上傳至資料庫', mutually_exclusive=['save2local'])
@argument('urls', nargs=-1)
def check(save2local, compare2local, urls, write2es):
    for url in urls:
        if save2local:
            with open(os.path.join(build_dir, f'{url.replace("/", "")}.txt'), 'w+', encoding='utf-8') as f:
                json.dump(combo(url), f, ensure_ascii=False)
        if compare2local:
            if os.path.exists(os.path.join(build_dir, f'{url.replace("/", "")}.txt')):
                with open(os.path.join(build_dir, f'{url.replace("/", "")}.txt'), 'r', encoding='utf-8') as f:
                    dict1 = ast.literal_eval(f.read())
                    dict2 = combo(url=url)
                    diff = {k: dict2[k] for k in set(dict2) - set(dict1)}
                    if len(diff) != 0:
                        print("The following keys have changed: " + diff.keys())
                        pprint(diff)
                    else:
                        print("Nothing on the web has changed.")
                        return
                    if write2es:
                        write2db(diff=diff)
            else:
                raise FileNotFoundError('File Not Found.')


def write2db(diff: typing.Dict[str, str]):
    es = browser_content.ElasticClient.get_instance()
    es.indices.create(index='web-change', ignore=400, body=map)
    es.index(index='test', body=diff)
    print(es.count(index='test'))


def combo(url: str) -> typing.Dict:
    dict = {}
    options = Options()
    options.headless = True
    browser = webdriver.Chrome(service=Service(
        ChromeDriverManager().install()), options=options)
    new = browser_content.BrowserContent(
        browser=browser, url=url)
    new.browser_init()
    dict['title'] = new.list_title()
    dict['meta-content'] = list(new.list_meta_contents())
    dict['class'] = list(new.list_classes())
    dict['id'] = list(new.list_ids())
    dict['heading-tag'] = list(new.list_heading_tags())
    dict['paragraph-tag'] = list(new.list_paragraph_tags())
    dict['hyperlink'] = list(new.list_hyperlinks())
    dict['whole-html'] = new.list_whole_html()
    return dict


if __name__ == '__main__':
    check()
