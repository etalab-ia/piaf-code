from typing import List, Union
from random import sample
from pathlib import Path
from os import makedirs
from json import JSONEncoder, dumps
import pickle as pkl
import sys

from wikipediaapi import Wikipedia, ExtractFormat


class Paragraph:
    def __init__(self,
                 context: str):
        self.context = context
        self.qas = []


class Article:
    def __init__(self,
                 title: str,
                 paragraphs: List[str]):
        self.title = title
        self.paragraphs = [Paragraph(p) for p in paragraphs]


class Dataset:
    class CustomEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__

    def __init__(self,
                 articles: List[Article],
                 version: str = 'frenchqa_1.0'):
        self.data = articles
        self.version = version

    def to_json(self):
        return dumps(self, indent=4, cls=self.CustomEncoder)


def dump_page(source: str,
              target_folder: Union[Path, str] = "pages",
              wiki_obj: Wikipedia = None,
              lang: str = 'fr'):
    if not wiki_obj:
        wiki_obj = Wikipedia(lang)

    target_folder = Path(target_folder)
    if not target_folder.exists():
        makedirs(target_folder)

    wikipage = wiki_obj.page(source)
    if not wikipage.exists():
        print(f"page {source} does not exist")


    else:
        page_info = wiki_obj.info(wikipage)
        if page_info.title != wikipage.title:
            wikipage = wiki_obj.page(page_info.title)
        wiki_title = wikipage.title.replace(' ', '_')
        target_file = target_folder / (wiki_title.replace("/", "__SLASH__") + ".pkl")
        pkl.dump(wikipage, target_file.open('wb'))


def main(path_topN_pkl):
    wiki_html = Wikipedia('fr', extract_format=ExtractFormat.HTML)
    wiki_page = Wikipedia('fr', extract_format=ExtractFormat.WIKI)

    sources = pkl.load(Path(path_topN_pkl).open('rb'))

    sources = [s[1].strip() for s in sources]

    for s in sources:
        dump_page(s, target_folder='data/10khtml', wiki_obj=wiki_html)
        dump_page(s, target_folder='data/10kpages', wiki_obj=wiki_page)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: \n python dump.py path_topN.pkl")
        exit(1)
    path_topN_pkl = sys.argv[1]

    main(path_topN_pkl)
