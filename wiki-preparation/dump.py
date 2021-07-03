from typing import  Literal, Optional
from pathlib import Path
from os import makedirs
import pickle as pkl

import click
from tqdm import tqdm
from wikipediaapi import Wikipedia, ExtractFormat


def mkdir_if_relevent(path: Path):
    if not path.exists():
        makedirs(path)



def dump_page(title: str,
              target_folder: Path,
              wikipedia: Wikipedia):
    wikipage = wikipedia.page(title)
    if not wikipage.exists():
        # TODO : Shouldn't raise ? 
        print(f"Page {title} does not exist")
        return
    wiki_title = wikipage.title.replace(' ', '_')
    target_file = target_folder / (wiki_title.replace("/", "__SLASH__") + ".pkl")
    pkl.dump(wikipage, target_file.open('wb'))

@click.command()
@click.option("-p", "--path-topn-pkl", type=str, help="Path to topN pkl")
@click.option("-n", "--number-of-sources", type=int,  help="Number of sources to dump", default = None)
def main(path_topn_pkl: str, number_of_sources: Optional[int] = None):
    wiki_html = Wikipedia('fr', extract_format=ExtractFormat.HTML)
    wiki_page = Wikipedia('fr', extract_format=ExtractFormat.WIKI)

    html_target_folder = Path('data/10khtml')
    mkdir_if_relevent(html_target_folder)
    pages_target_folder = Path('data/10kpages')
    mkdir_if_relevent(pages_target_folder)

    sources = pkl.load(Path(path_topn_pkl).open('rb'))
    number_of_sources = number_of_sources or len(sources)
    sources = [s[1].strip() for s in sources[:number_of_sources]]
    for s in tqdm(sources):
        dump_page(s, target_folder=html_target_folder, wikipedia=wiki_html)
        dump_page(s, target_folder=pages_target_folder, wikipedia=wiki_page)


if __name__ == "__main__":
    main()
