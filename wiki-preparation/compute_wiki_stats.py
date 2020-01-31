import pickle as pkl
import numpy as np
import wikipediaapi
import matplotlib.pyplot as plt
import argparse

from wikipediaapi import Wikipedia
from tqdm import tqdm
from os import listdir


# We want to save the articles stats

def get_section_text(section, level=1):
    s_text = ''
    for s in section.sections:
        s_text += s.text
        s_text += '\n' + get_section_text(s, level + 1)
    return s_text


def compute_article(wiki_path, html_path):
    stats = {}
    wiki_path = wiki_path.replace(' ', '_')
    html_path = html_path.replace(' ', '_')

    with open(wiki_path, 'rb') as f:
        page = pkl.load(f)

    if html_path is not None:
        with open(html_path, 'rb') as f:
            page_html = pkl.load(f)
    try:
        stats['total_text_length'] = len(page.text)
    except:
        print(wiki_path)
        print('TextError')
        return 'TextError'

    stats['draft_in_category'] = False
    stats['homonym_in_category'] = False

    try:
        for category in page.categories:
            if 'Catégorie:Wikipédia:ébauche' in category:
                stats['draft_in_category'] = True
            if 'Catégorie:Homonymie' in category:
                stats['homonym_in_category'] = True
    except:
        print('CategoryError')
        return 'CategoryError'
    # Now we crawl over the text section by section
    stats['sections_length'] = []
    stats['paragraph_length_by_sections'] = []
    stats['paragraph_by_sections'] = []
    stats['summary_length'] = len(page.summary)

    # First the summary (not included in the sections)

    try:
        summary_paragraphs = page.summary.split('\n')
    except:
        print('SummaryError')
        return 'SummaryError'
    stats['paragraph_length_by_summary'] = [len(paragraph) for paragraph in summary_paragraphs]
    stats['paragraphs_in_summary'] = summary_paragraphs
    stats['section_titles'] = []
    # Now the real sections

    stats['is_a_year_article'] = False

    try:
        for i, section in enumerate(page.sections):
            if section.title in ['Voir aussi', 'Articles connexes', 'Liens externes', 'Notes et références']:
                break
            if section.title == 'Événements':
                stats['is_a_year_article'] = True

            # We check if the section contains lists 

            if html_path is not None:
                if '<li>' in page_html.sections[i].text:
                    current_section_text = ''
                else:
                    current_section_text = section.text + '\n'

                new_html_section_text = get_section_text(page_html.sections[i])

                if '<li>' in new_html_section_text:
                    new_section_text = ''
                else:
                    new_section_text = get_section_text(section)

                section_text = current_section_text + new_section_text
            else:
                section_text = section.text + '\n' + get_section_text(section)

            stats['sections_length'].append(len(section_text))

            paragraphs = section_text.split('\n')
            paragraph_length_by_section = [len(paragraph) for paragraph in paragraphs]
            stats['paragraph_length_by_sections'].append(paragraph_length_by_section)
            stats['paragraph_by_sections'].append([paragraph for paragraph in paragraphs])
            stats['section_titles'].append(section.title)
    except:
        print('SectionError')
        return 'SectionError'
    return stats


def compute_files(wiki_path_list, folder_path, html_path):
    if html_path is not None:
        stats_dic = {wiki_path: compute_article(folder_path + '/' + wiki_path, html_path + '/' + wiki_path) for
                     wiki_path in tqdm(wiki_path_list)}
    else:
        stats_dic = {wiki_path: compute_article(folder_path + '/' + wiki_path, None) for wiki_path in
                     tqdm(wiki_path_list)}
    return stats_dic


def get_pkl_filenames_from_folder(folder_path):
    list_files = [f for f in listdir(folder_path) if '.pkl' in f]
    return list_files


def main():
    parser = argparse.ArgumentParser()
    ## Required parameters
    parser.add_argument("--folder_path", default=None, type=str, required=True,
                        help="Path where the pages are saved")

    parser.add_argument("--html_path", default=None, type=str, required=False,
                        help="Path where the html pages are saved")

    parser.add_argument("--output_dic_fn", default=None, type=str, required=True,
                        help="Pkl file where the stats will be dumped")

    args = parser.parse_args()

    wiki_path_list = get_pkl_filenames_from_folder(args.folder_path)

    stats_dic = compute_files(wiki_path_list, args.folder_path, args.html_path)

    with open(args.output_dic_fn, 'wb') as f:
        pkl.dump(stats_dic, f)


if __name__ == "__main__":
    main()
