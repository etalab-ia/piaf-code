from dataclasses import dataclass
from glob import glob
from pathlib import Path
from typing import Any, Dict, List, NewType, Optional

import click
from tqdm import tqdm
from wikipediaapi import WikipediaPageSection


from utils import load_pickle, dump_pickle


def get_section_text(section: WikipediaPageSection, level=1):
    s_text = ""
    for s in section.sections:
        s_text += s.text
        s_text += "\n" + get_section_text(s, level + 1)
    return s_text


Paragraph = NewType("Paragraph", Any)
PageSummary = NewType("PageSummary", Any)


@dataclass
class WikiStat:
    total_text_length: int
    draft_in_category: bool
    homonym_in_category: bool
    is_a_year_article: bool
    sections_length: List[int]
    paragraph_length_by_sections: List[int]
    paragraph_length_by_summary: List[int]
    paragraph_by_sections: List[Paragraph]
    summary_length: int
    paragraphs_in_summary: PageSummary
    section_titles: List[str]


section_titles_to_ignore = [
    "Voir aussi",
    "Articles connexes",
    "Liens externes",
    "Notes et références",
]


def prepare_section_with_links_to_html(
    section: WikipediaPageSection,
    section_from_html_page: Optional[WikipediaPageSection],
) -> str:
    if not section_from_html_page:
        return section.text + "\n" + get_section_text(section)

    if "<li>" in section_from_html_page.text:
        current_section_text = ""
    else:
        current_section_text = section.text + "\n"

    new_html_section_text = get_section_text(section_from_html_page)

    if "<li>" in new_html_section_text:
        new_section_text = ""
    else:
        new_section_text = get_section_text(section)

    return current_section_text + new_section_text


def compute_wiki_stat(wiki_path: Path, html_path: Optional[Path]) -> Optional[WikiStat]:

    wiki_page = load_pickle(wiki_path)
    html_sections = load_pickle(html_path).sections if html_path else None

    summary_paragraphs = wiki_page.summary.split("\n")

    wiki_sections_of_interrest = [
        wiki_section
        for wiki_section in wiki_page.sections
        if wiki_section.title not in section_titles_to_ignore
    ]
    wiki_sections_of_interrest_titles = [
        wiki_section.title for wiki_section in wiki_sections_of_interrest
    ]
    wiki_section_texts = [
        prepare_section_with_links_to_html(wiki_section, html_section)
        for wiki_section, html_section in zip(wiki_sections_of_interrest, html_sections)
    ]

    paragraph_by_section = [
        section_text.split("\n") for section_text in wiki_section_texts
    ]

    return WikiStat(
        total_text_length=len(wiki_page.text),
        draft_in_category="Catégorie:Wikipédia:ébauche" in wiki_page.categories,
        is_a_year_article="Événements" in wiki_sections_of_interrest_titles,
        homonym_in_category="Catégorie:Homonymie" in wiki_page.categories,
        summary_length=len(wiki_page.summary),
        paragraphs_in_summary=summary_paragraphs,
        paragraph_length_by_summary=[
            len(paragraph) for paragraph in summary_paragraphs
        ],
        sections_length=[len(section_text) for section_text in wiki_section_texts],
        section_titles=wiki_sections_of_interrest_titles,
        paragraph_by_sections=paragraph_by_section,
        paragraph_length_by_sections=[
            len(paragraph) for paragraph in paragraph_by_section
        ],
    )


def compute_wiki_stats(
    wiki_paths: List[Path], html_paths: Optional[List[Path]]
) -> Dict[str, WikiStat]:
    wiki_stats = {}
    for i, wiki_path in tqdm(enumerate(wiki_paths)):
        wiki_stats[wiki_path.name] = compute_wiki_stat(
            wiki_path, html_paths[i] if html_paths else None
        )
    return wiki_stats


@click.command()
@click.option(
    "--input-wiki-pkl",
    default=None,
    type=str,
    required=True,
    help="Pickle file where the wiki pages are saved",
)
@click.option(
    "--input-html-pkl",
    default=None,
    type=str,
    required=False,
    help="Pickle file where the HTML pages are saved",
)
@click.option(
    "--output-wiki-stat-pkl",
    default=None,
    type=str,
    required=True,
    help="Pkl file where the wiki stats will be dumped",
)
@click.option(
    "--n-pages",
    default=None,
    type=int,
    required=True,
    help="Number of pages to compute stats on ",
)
def main(
    input_wiki_pkl: str,
    input_html_pkl: str,
    output_wiki_stat_pkl: str,
    n_pages: Optional[int] = None,
):
    input_wiki_path = Path(input_wiki_pkl)
    input_html_path = Path(input_html_pkl)

    wiki_file_names = [Path(f).name for f in glob(str(input_wiki_path / "*.pkl"))]
    wiki_paths = [
        input_wiki_path / wiki_file_name for wiki_file_name in wiki_file_names
    ]
    html_paths = [
        input_html_path / wiki_file_name for wiki_file_name in wiki_file_names
    ]

    n_pages = n_pages or len(wiki_paths)
    wiki_stats = compute_wiki_stats(wiki_paths[:n_pages], html_paths)
    dump_pickle(output_wiki_stat_pkl, wiki_stats)


if __name__ == "__main__":
    main()

# python compute_wiki_stats.py --input-wiki-pkl data/10kpages --input-html-pkl data/10khtml --output-wiki-stat-pkl stats_topN.pkl --n-pages 2
