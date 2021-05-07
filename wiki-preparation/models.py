from dataclasses import dataclass, asdict
from typing import List
from json import dumps

@dataclass
class Paragraph: 
    context: str
    qas: List = []


@dataclass
class Article: 
    title: str
    paragraphs: List[Paragraph]
    oldid: str


@dataclass
class Dataset:
    articles: List[Article]
    version: str = "frenchqa_1.0"

    def to_json(self):
        return dumps(asdict(self))


