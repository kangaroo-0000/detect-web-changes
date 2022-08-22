import browser_content
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from pprint import pprint
from click import command, option, argument, Option, UsageError
import typing
import os
import ast
import json


map = {
    "settings": {
        "number_of_shards": 2,
        "number_of_replicas": 1
    },
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
options = Options()
options.headless = True


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
                ' 提示: 此參數與下列參數互斥：[' + ex_str + '].'
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise UsageError(
                f"Illegal usage: \"{self.name}\" is mutually exclusive with argument(s) \"{', '.join(self.mutually_exclusive)}\". For more info, type \"--help\"."
            )

        return super(MutuallyExclusiveOption, self).handle_parse_result(
            ctx,
            opts,
            args
        )


@ command()
@ option('-s', '--save2local', is_flag=True, cls=MutuallyExclusiveOption, help='輸入網站URL，並存取該網站HTML到本地資料夾', mutually_exclusive=['compare2local', 'write2es'])
@ option('-c', '--compare2local', is_flag=True, cls=MutuallyExclusiveOption, help='輸入網站URL，並與本地的對應資料比對該網站HTML有無更新', mutually_exclusive=['save2local'])
@ option('-w', '--write2es', is_flag=True, cls=MutuallyExclusiveOption, help='將比對不同之處上傳至OpenSearch資料庫', mutually_exclusive=['save2local'])
@ argument('urls', nargs=-1)
def check(save2local, compare2local, urls, write2es):
    for url in urls:
        browser = webdriver.Chrome(service=Service(
            ChromeDriverManager().install()), options=options)
        new = browser_content.BrowserContent(
            browser=browser, url=url)
        s = browser_content.SaveAsPlainText(
            path=build_dir, filename=f'{url.replace("/", "")}.txt', browser_content=new)
        # spdf = browser_content.SaveAsPDF(
        #     path=build_dir, filename=f'{url.replace("/", "")}.pdf', browser_content=new)
        if save2local:
            s.save()
            # spdf.save()
        if compare2local:
            if os.path.exists(os.path.join(build_dir, f'{url.replace("/", "")}.txt')):
                with open(os.path.join(build_dir, f'{url.replace("/", "")}.txt'), 'r', encoding='utf-8') as f:
                    dict1 = ast.literal_eval(f.read())
                    dict2 = s.get_text_2b_saved()
                    diff = {}
                    diffkeys = [k for k in dict1 if dict1.get(k)
                                != dict2.get(k) and k != "timestamp"]
                    for k in diffkeys:
                        diff[k] = list(set(dict1[k]) ^ set(dict2[k]))
                    if len(diff) != 0:
                        print("The following keys have changed: " +
                              str(diff.keys()))
                        pprint(diff)
                    else:
                        print(
                            "Nothing on the web has changed. Nothing will be written to the database.")
                        return
                    if write2es:
                        write2db(diff=diff)
            else:
                raise FileNotFoundError('File Not Found.')


def write2db(diff: typing.Dict[str, str]):

    es = browser_content.ElasticClient.get_instance()
    if not es.ping:
        raise ValueError("Connection Failed.")
    es.indices.create(
        index='web-change-log', ignore=400, body=map)
    es.index(
        index='web-change-log', body=json.dumps(diff))


if __name__ == '__main__':
    check()
