import browser_content
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from pprint import pprint
from click import command, option, argument, Option, UsageError
import difflib
import typing
import os
import ast
import json
import re
from datetime import datetime, timezone


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
            },
            "hash": {
                "type": "text"
            }
        }
    }
}


def new_dump(self, tag, x, lo, hi):
    """
    補丁(monkeypatch) difflib 的 dump 方法 
    """
    if tag == "+":
        tag = "被刪除"
    elif tag == "-":
        tag = "新增"
    for i in range(lo, hi):
        yield '%s %s' % (tag, x[i])


build_dir = "../web_result/"
options = Options()
options.headless = True
difflib.Differ._dump = new_dump
d = difflib.Differ()


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
@ option('-s', '--save_html', is_flag=True, cls=MutuallyExclusiveOption, help='輸入網站URL，並存取該網站HTML到本地資料夾', mutually_exclusive=['compare2local', 'write2es'])
@ option('-c', '--compare_html', is_flag=True, cls=MutuallyExclusiveOption, help='輸入網站URL，並與本地的對應資料比對該網站HTML有無更新', mutually_exclusive=['save2local'])
@ option('-a', '--compare_tag', is_flag=True, help='輸入網站URL，將與本地對應資料進行HTML標籤比對')
@ option('-i', '--compare_hash', is_flag=True)
@ option('-w', '--write2es', is_flag=True, cls=MutuallyExclusiveOption, help='將比對不同之處上傳至OpenSearch資料庫', mutually_exclusive=['save2local'])
@ option('-t', '--specify_tag', type=str, multiple=True)
@ option('-o', '--save_tags', is_flag=True, cls=MutuallyExclusiveOption, help='存取該網站較重要標籤', mutually_exclusive=['compare2local', 'write2es', 'specify_tag'])
@ option('-h', '--hash_html', is_flag=True, help='對HTML進行哈希算法並存取之')
@ argument('urls', nargs=-1)
def check(save_html, compare_html, compare_tag, urls, write2es, specify_tag, hash_html, save_tags, compare_hash):
    for url in urls:
        browser = webdriver.Chrome(service=Service(
            ChromeDriverManager().install()), options=options)
        new = browser_content.BrowserContent(
            browser=browser, url=url)
        path = os.path.join(build_dir, url.replace("/", ""))
        if not os.path.exists(path):
            os.makedirs(path)
        if save_html:
            s = browser_content.SaveHTMLAsPlainText(
                path=path, filename='html.txt', browser_content=new)
            s.save()
        if save_tags:
            st = browser_content.SaveTagsAsPlainText(
                path=path, filename='tags.txt', browser_content=new)
            st.save()
        if hash_html:
            sh = browser_content.SaveHTMLAsHash(
                path=path, filename='hash.txt', browser_content=new)
            sh.save()
        if compare_html:
            s = browser_content.SaveHTMLAsPlainText(
                path=path, filename='html.txt', browser_content=new)
            if os.path.exists(os.path.join(path, 'html.txt')):
                with open(os.path.join(path, 'html.txt'), 'r', encoding='utf-8') as f:
                    original = f.read()
                    new_html = s.get_html_2b_saved()
                    print(new_html)
                    for index, s in enumerate(difflib.ndiff(original, new_html)):
                        if s[0] == ' ':
                            continue
                        elif s[0] == '被':
                            print(f'Delete "{s[-1]}" from position {index}')
                        elif s[0] == '新':
                            print(f'Add "{s[-1]}" to position {index}')
                    if write2es:
                        html_diff = {}
                        html_diff["whole-html"] = [l for l in difflib.ndiff(
                            original, new_html) if not l.startswith(" ")]
                        html_diff["@timestamp"] = datetime.now(
                            timezone.utc).isoformat()
                        write2db(diff=html_diff)

            else:
                raise FileNotFoundError('本地資料尚無此網站檔案。請先進行網站資料存取再進行比對。')
        if compare_tag:
            st = browser_content.SaveTagsAsPlainText(
                path=path, filename='tags.txt', browser_content=new)
            if os.path.exists(os.path.join(path, 'tags.txt')):
                with open(os.path.join(path, 'tags.txt'), 'r', encoding='utf-8') as f:
                    dict1 = ast.literal_eval(f.read())
                    dict2 = st.get_text_2b_saved()
                    diff = {}
                    diffkeys = [k for k in dict1 if dict1.get(k)
                                != dict2.get(k)]
                    for k in diffkeys:
                        diff[k] = [l for l in d.compare(
                            dict1.get(k), dict2.get(k)) if not l.startswith(" ")]
                    if len(diff) != 0:
                        print("The following keys have changed: " + str(diffkeys))
                        pprint(diff)
                    else:
                        print(
                            "Nothing on the web has changed. Nothing will be written to the database.")
                        return
                    if write2es:
                        diff["@timestamp"] = datetime.now(
                            timezone.utc).isoformat()
                        write2db(diff=diff)
            else:
                raise FileNotFoundError('本地資料尚無此網站檔案。請先進行網站資料存取再進行比對。')
        if compare_hash:
            sh = browser_content.SaveHTMLAsHash(
                path=path, filename='hash.txt', browser_content=new)
            if os.path.exists(os.path.join(path, 'hash.txt')):
                with open(os.path.join(path, 'hash.txt'), 'r', encoding='utf-8') as f:
                    if f.read() == sh.get_hash_2b_saved():
                        print(
                            "Hash remains the same. No changes had taken place on this web.")
                    else:
                        print("Hash changed!")
                        print(f'New Hash: {sh.get_hash_2b_saved}')
                        print(f'Old Hash: {f.read()}')


def write2db(diff: typing.Union[typing.Dict[str, str], typing.List[str]]):

    es = browser_content.ElasticClient.get_instance()
    if not es.ping:
        raise ValueError("Connection to OpenSearch Database Failed.")
    es.indices.create(
        index='web-change-log', ignore=400, body=map)
    es.index(
        index='web-change-log', body=json.dumps(diff))


def convertHtml2Xpath(html: str):
    html.replace("<", "")
    html.replace(">", "")
    xpath = re.search("([\w\s]+)=([\w\s\"]+)", html)
    tag = xpath[1]
    attribute = xpath[2]


if __name__ == '__main__':
    check()
