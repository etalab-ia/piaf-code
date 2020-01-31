import pickle as pkl
import numpy as np
import matplotlib.pyplot as plt
import random
from tqdm import tqdm
import argparse
from typing import List
from json import JSONEncoder, dumps

from wikipediaapi import Wikipedia


class Paragraph:
    def __init__(self,
                 context: str):
        self.context = context
        self.qas = []


class Article:
    def __init__(self,
                 title: str,
                 paragraphs: List[str],
                 oldid: str):
        self.title = title
        self.paragraphs = [Paragraph(p) for p in paragraphs]
        self.oldid = oldid


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


def check_number_paragraphs(article_stats, min_len_paragraphs=500, max_len_paragraphs=1000):
    if article_stats['total_text_length'] < min_len_paragraphs:
        return []
    # We do flatten the para by section list that is composed of a list of section, and a section being a list 
    # of paragraphs. This list by section was done this way to also study context length by section
    flatten_section = [para for section in article_stats['paragraph_length_by_sections'] for para in section]
    all_paras = article_stats['paragraph_length_by_summary'] + flatten_section
    all_paras_filtered = [para for para in all_paras if para >= min_len_paragraphs and para < max_len_paragraphs]

    return all_paras_filtered


def get_number_paragraphs(stats_all_articles, min_len_paragraphs=500):
    nb_paragraphs = [len(check_number_paragraphs(article_stats, min_len_paragraphs)) for article_stats in
                     stats_all_articles.values()]
    return nb_paragraphs


def compute_min_len_paras_on_dic(article_stats, min_len_paragraphs=500, max_len_paragraphs=1000):
    article_stats['paras'] = check_number_paragraphs(article_stats, min_len_paragraphs, max_len_paragraphs)

    return article_stats


def filter_article_by_categories(article_stats, draft=False, homonym=False):
    try:
        if article_stats['homonym_in_category'] == homonym:
            if article_stats['draft_in_category'] == draft:
                return True
        return False
    except:
        return False


def filter_dic(stats, min_len_paragraphs=500, draft=False, homonym=False, max_len_paragraphs=1000):
    filtered_dic = {filename: check_number_paragraphs(stats[filename], min_len_paragraphs, max_len_paragraphs) for
                    filename in stats if filter_article_by_categories(stats[filename], draft, homonym)}
    return filtered_dic


def print_para_if_max(stats, max_para_len=8000):
    for filename in stats:
        for para in stats[filename]:
            if para > max_para_len:
                print(filename, para)


def filter_min_paras(stats_with_para_len, min_nb_paras):
    filtered_dic = {filename: stats_with_para_len[filename] for filename in stats_with_para_len if
                    len(stats_with_para_len[filename]) >= min_nb_paras}
    return filtered_dic


def get_section_text(section, level=1):
    s_text = ''
    for s in section.sections:
        s_text += s.text
        s_text += '\n' + get_section_text(s, level + 1)
    return s_text


def filter_years_articles(page_pkl_fn):
    # If 'Evenements' is in sections title, then it means it is a year article.
    with open(page_pkl_fn, 'rb') as f:
        page = pkl.load(f)

    for section in page.sections:
        if section.title in ['Événements']:
            return False
        return True


def get_section_paragraphs_text(page_pkl_fn, min_len_para=500, max_len_para=1000, wiki_path=None, html_path=None):
    if wiki_path is None:
        wiki_path = ''
    with open(wiki_path + '/' + page_pkl_fn, 'rb') as f:
        page = pkl.load(f)

    if html_path is not None:
        with open(html_path + '/' + page_pkl_fn, 'rb') as f:
            page_html = pkl.load(f)

    paragraphs = [paragraph for paragraph in page.summary.split('\n') if
                  len(paragraph) >= min_len_para and len(paragraph) < max_len_para]
    for i, section in enumerate(page.sections):
        if section.title in ['Voir aussi', 'Articles connexes', 'Liens externes', 'Notes et références']:
            break

        # We check if the section contains lists 
        if html_path is not None and '<li>' in page_html.sections[i].text:
            current_section_text = ''
            new_html_section_text = get_section_text(page_html.sections[i])
        else:
            current_section_text = section.text + '\n'
            new_html_section_text = current_section_text

        if html_path is not None and '<li>' in new_html_section_text:
            new_section_text = ''
        else:
            new_section_text = get_section_text(section)

        section_text = current_section_text + new_section_text

        for paragraph in section_text.split('\n'):
            if len(paragraph) >= min_len_para and len(paragraph) < max_len_para:
                paragraphs.append(paragraph)
    return paragraphs


def get_filtered_complete_dic(pkl_with_stats_fn, min_paragraphs=5, min_len_paragraphs=500, max_len_paragraphs=1000,
                              draft=False, homonym=False, years=False, wiki_path=None, clean_duplicates=False):
    with open(pkl_with_stats_fn, 'rb') as f:
        stats_uncleaned = pkl.load(f)

    # We filter out the sections errors    
    stats = {key: stats_uncleaned[key] for key in stats_uncleaned if stats_uncleaned[key] != 'SectionError'}

    filtered_stats = filter_dic(stats, min_len_paragraphs=min_len_paragraphs, draft=draft, homonym=homonym,
                                max_len_paragraphs=max_len_paragraphs)
    filtered_stats = filter_min_paras(filtered_stats, min_paragraphs)

    # We filter the years

    if clean_duplicates:
        if wiki_path is None:
            print("Error : give a wikipath for duplicates cleaning")
            return
        new_ft_stats = {}
        wiki_obj = Wikipedia('fr')
        for filename, stats in filtered_stats.items():
            try:
                with open(wiki_path + '/' + filename, 'rb') as f:
                    page = pkl.load(f)
            except FileNotFoundError:
                print("Not found :" + filename)
                continue
            page_info = wiki_obj.info(page)
            new_title = title = page_info.title
            new_title = new_title.replace(' ', '_')
            new_title += '.pkl'
            new_ft_stats[new_title] = stats
        filtered_stats = new_ft_stats

    if not years:
        print("Length before year fitering :", len(filtered_stats))
        if wiki_path is None:
            filtered_stats = {filename: filtered_stats[filename] for filename in filtered_stats if
                              filter_years_articles(filename)}
        else:
            filtered_stats = {filename: filtered_stats[filename] for filename in filtered_stats if
                              filter_years_articles(wiki_path + filename)}
    print("Final length : ", len(filtered_stats))
    return filtered_stats


def main():
    parser = argparse.ArgumentParser()
    ## Required parameters
    parser.add_argument("--pkl_stats_dic_fn", default=None, type=str, required=True,
                        help="Pkl file where the stats are already dumped")

    parser.add_argument("--output_json_article_fn", default=None, type=str, required=True,
                        help="output_json_article_fn")

    parser.add_argument("--min_paragraphs", default=5, type=int, required=False,
                        help="Minimum number of paragraphs per article")

    parser.add_argument("--min_len_paragraphs", default=500, type=int, required=False,
                        help="Minimum len of paragraphs")

    parser.add_argument("--max_len_paragraphs", default=1000, type=int, required=False,
                        help="Max len of paragraphs")

    parser.add_argument("--nb_articles_to_print", default=None, type=int, required=False,
                        help="Number of articles to print if output_json_article_fn is not None")

    parser.add_argument("--wiki_path", default=None, type=str, required=True,
                        help="Path to where the wiki pages are saved")
    parser.add_argument("--html_path", default=None, type=str, required=True,
                        help="Path to where the html pages are saved")

    args = parser.parse_args()

    stats = get_filtered_complete_dic(args.pkl_stats_dic_fn, min_paragraphs=args.min_paragraphs,
                                      min_len_paragraphs=args.min_len_paragraphs,
                                      max_len_paragraphs=args.max_len_paragraphs, draft=False, homonym=False,
                                      years=True, wiki_path=args.wiki_path, clean_duplicates=False)

    if args.output_json_article_fn is not None:

        articles_filename = list(stats.keys())
        random.shuffle(articles_filename)

        if args.nb_articles_to_print is not None:
            articles_filename = articles_filename[:args.nb_articles_to_print]

        articles_list = []
        for article_fn in tqdm(articles_filename):
            try:
                paragraphs = get_section_paragraphs_text(article_fn, min_len_para=args.min_len_paragraphs,
                                                         max_len_para=args.max_len_paragraphs, wiki_path=args.wiki_path,
                                                         html_path=args.html_path)
                filename = article_fn.split('/')[-1]
            except FileNotFoundError:
                continue
                # File may have been deleted already because it was a duplicate

            with open(args.wiki_path + '/' + filename, 'rb') as f:
                page = pkl.load(f)

            filename = filename.replace('_', ' ')
            filename = filename.replace('.pkl', '')

            articles_list.append(Article(filename, paragraphs, oldid=str(page.lastrevid)))

        dataset = Dataset(articles_list)

        with open(args.output_json_article_fn, 'w') as f:
            f.write(dataset.to_json())


if __name__ == "__main__":
    main()
