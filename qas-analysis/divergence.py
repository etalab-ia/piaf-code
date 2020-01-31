# coding: utf-8

from french_divergences import *
from spacy.lang.fr import French
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import sys


def get_french_distances(dataset_fn):
    pipeline = French()
    sentencizer = pipeline.create_pipe('sentencizer')
    pipeline.add_pipe(sentencizer)

    questions_list, sentences_list, spans_list = compute_question_sentence(dataset_fn, pipeline)

    nlp_fr = spacy.load('fr_core_news_sm')

    all_distances = []
    error = 0
    error_anchor = 0
    no_pronoums = 0
    all_lexical_variation = []
    for i, question in enumerate(questions_list):
        try:
            print(questions_list[i], sentences_list[i], spans_list[i])
            distance, lexical_variation = get_anchor(questions_list[i], sentences_list[i], nlp_fr, spans_list[i])
            if distance is not None:
                if distance == -1:
                    error_anchor += 1
                elif distance == -2:
                    no_pronoums += 1
                else:
                    all_distances.append(distance)
                    all_lexical_variation.append(lexical_variation)
        except:
            error += 1
            continue
    print(error, error_anchor, no_pronoums)
    return all_distances, all_lexical_variation


def main(path_piaf_dataset):
    all_distances, all_lexical_variation = get_french_distances(path_piaf_dataset)

    plt.hist(all_distances, bins=[0, 1, 2, 3, 4, 5, 6, 7, 8], weights=np.ones(len(all_distances)) / len(all_distances))
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
    plt.xlabel('Syntactic divergence')
    plt.ylabel('Percentage')
    plt.savefig('hits_syntaxic.pdf')

    plt.clf()

    plt.hist(all_lexical_variation, weights=np.ones(len(all_lexical_variation)) / len(all_lexical_variation))
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
    plt.xlabel('Lexical variation')
    plt.ylabel('Percentage of questions')
    plt.savefig('lexical_variation_piaf_by_tokens_lemma.pdf')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:\n python divergence.py path_piaf_dataset_json ")
        exit(1)
    path_piaf_dataset = sys.argv[1]

    main(path_piaf_dataset)
