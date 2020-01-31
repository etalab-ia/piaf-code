import json
import os
import sys
import numpy as np
import spacy
import networkx
import editdistance
import networkx as nx

import re


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def get_question_answers_sentences(dataset_fn, output_folder, pipeline, dump_answers=False):
    with open(dataset_fn, 'r') as f:
        dataset = json.load(f)
    total_answer = 0
    f_span = open(output_folder + 'qr.csv', 'w')
    f_sentence = open(output_folder + 'qr_sentence.csv', 'w')
    try:
        os.mkdir(output_folder + 'docs')
    except FileExistsError:
        print('Folder exitsts')

    for article in dataset['data']:
        # We will join the paragraphs
        article_text = ''
        article['title'] = cleanhtml(article['title'])

        for paragraph in article['paragraphs']:
            context = paragraph['context']
            article_text += context
            article_text += '\n'
            if not dump_answers:
                continue

            doc = pipeline(context)
            start_sent = 0
            start_to_sentence = {}
            for sent in doc.sents:
                # print(start_sent, len(sent.text))
                end_sent = start_sent + len(sent.text) + 1
                for i in range(start_sent, end_sent):
                    start_to_sentence[i] = sent.text
                    start_sent = end_sent

            for qa in paragraph['qas']:
                question = qa['question']
                answer = qa['answers'][0]

                answer_span = answer['text']
                answer_span = answer_span.strip(' ')
                answer_span = answer_span.strip('.')
                answer['answer_start'] = paragraph['context'].find(answer_span)
                answer_sentence = start_to_sentence[answer['answer_start']]
                if answer_sentence.find(answer_span) < 0:
                    print("Error")
                    print(answer_span + ' fin', answer_sentence)
                    continue
                else:
                    total_answer += 1
                f_sentence.write(question + '\t' + answer_sentence + '\t' + str(article['title']) + '\n')
                f_span.write(question + '\t' + answer_span + '\t' + str(article['title']) + '\n')

        with open(output_folder + 'docs/' + article['title'] + '.txt', 'w') as f:
            f.write(article_text)
    f_sentence.close()
    f_span.close()
    print(total_answer)


def compute_question_sentence(dataset_fn, pipeline):
    questions_list = []
    sentences_list = []
    answers_list = []

    unfound_cpt = 0

    with open(dataset_fn, 'r') as f:
        dataset = json.load(f)

    for article in dataset['data']:
        # We will join the paragraphs

        for paragraph in article['paragraphs']:

            doc = pipeline(paragraph['context'])
            start_sent = 0
            start_to_sentence = {}
            for sent in doc.sents:
                # print(start_sent, len(sent.text))
                end_sent = start_sent + len(sent.text) + 1
                for i in range(start_sent, end_sent):
                    start_to_sentence[i] = sent.text
                    start_sent = end_sent

            for qa in paragraph['qas']:
                question = qa['question']
                if not qa['answers']:
                    continue
                answer = qa['answers'][0]

                answer_span = answer['text']
                answer_sentence = start_to_sentence[answer['answer_start']]

                if answer_sentence.find(answer['text']) < 0:
                    print(question, answer)
                    unfound_cpt += 1
                    continue
                answers_list.append(answer_span)
                questions_list.append(question)
                sentences_list.append(answer_sentence)
    print(unfound_cpt)
    return questions_list, sentences_list, answers_list


def get_anchor(question, answer, nlp, span):
    # We tokenize the sentences
    # questions_pronoums=['what', 'where', 'when', 'why', 'how', 'who', 'which']
    questions_pronoums = ['quelle', 'que', 'où', 'combien', 'quel', 'qui', 'quand', 'comment', 'quoi', 'pourquoi',
                          'Quand', 'quell']

    doc_question = nlp(question)
    doc_answer = nlp(answer)
    tokens_questions = []
    tokens_answers = []

    for token in doc_answer:
        tokens_answers.append(token.lemma_)

    for token in doc_question:
        tokens_questions.append(token.lemma_)

    anchors = [token for token in tokens_questions if token in tokens_answers]

    lexical_variation = 1 - len(anchors) / len(tokens_questions)

    if len(anchors) == 0:
        # print("No anchor")
        return -1, lexical_variation

    # Question iteration
    qdoc_child2head_dic = {}
    qdoc_head2child_dic = {}
    qlemma_to_id = {}
    edges_question = []

    pronom_question = None
    for token in doc_question:
        # print(token.lemma_)
        if token.lemma_ in questions_pronoums:
            pronom_question = token.lemma_
        if token.lemma_ in qlemma_to_id:
            qlemma_to_id[token.lemma_].append('{0}-{1}'.format(token.lemma_, token.i))
        else:
            qlemma_to_id[token.lemma_] = ['{0}-{1}'.format(token.lemma_, token.i)]
        # FYI https://spacy.io/docs/api/token
        qdoc_head2child_dic['{0}-{1}'.format(token.lemma_, token.i)] = {}
        for child in token.children:
            child_value = '{0}-{1}'.format(child.lemma_, child.i)
            head_value = '{0}-{1}'.format(token.lemma_, token.i)
            qdoc_head2child_dic[head_value][child_value] = child.dep_

            if child_value not in qdoc_child2head_dic:
                qdoc_child2head_dic[child_value] = {}
            qdoc_child2head_dic[child_value][head_value] = child.dep_
            edges_question.append(('{0}-{1}'.format(token.lemma_, token.i),
                                   '{0}-{1}'.format(child.lemma_, child.i)))

    if pronom_question is None:
        # print(question)
        # print(tokens_questions)

        return -2, lexical_variation

    # Answer iteration
    adoc_child2head_dic = {}
    adoc_head2child_dic = {}
    alemma_to_id = {}
    edges_answer = []
    lemma_to_word = {}

    for token in doc_answer:
        lemma_to_word['{0}-{1}'.format(token.lemma_, token.i)] = token.text
        if token.lemma_ in alemma_to_id:
            alemma_to_id[token.lemma_].append('{0}-{1}'.format(token.lemma_, token.i))
        else:
            alemma_to_id[token.lemma_] = ['{0}-{1}'.format(token.lemma_, token.i)]
        # FYI https://spacy.io/docs/api/token
        adoc_head2child_dic['{0}-{1}'.format(token.lemma_, token.i)] = {}
        for child in token.children:
            child_value = '{0}-{1}'.format(child.lemma_, child.i)
            head_value = '{0}-{1}'.format(token.lemma_, token.i)
            adoc_head2child_dic[head_value][child_value] = child.dep_

            if child_value not in adoc_child2head_dic:
                adoc_child2head_dic[child_value] = {}
            adoc_child2head_dic[child_value][head_value] = child.dep_
            adoc_head2child_dic['{0}-{1}'.format(token.lemma_, token.i)][
                '{0}-{1}'.format(child.lemma_, child.i)] = child.dep_
            edges_answer.append(('{0}-{1}'.format(token.lemma_, token.i),
                                 '{0}-{1}'.format(child.lemma_, child.i)))

    graph_question = nx.Graph(edges_question)
    graph_answer = nx.Graph(edges_answer)

    # We find the answer to be anchored to : it is the token of the answer that has no parent within the answer
    answer_to_anchor = None
    for answer_lemma in adoc_child2head_dic:
        if span.find(lemma_to_word[answer_lemma]) >= 0:
            # print('found', answer_lemma)

            parent = list(adoc_child2head_dic[answer_lemma].keys())[0]
            if span.find(lemma_to_word[parent]) < 0:
                # No parent
                answer_to_anchor = answer_lemma
                break

    if answer_to_anchor is None:
        print("Bug answer to anchor")
        print(adoc_child2head_dic, span)
        return None, lexical_variation

    all_edit_distances = []
    # No we iterate over the anchors to find the shortest edit distance
    for anchor in anchors:

        paths = nx.shortest_path(graph_question, qlemma_to_id[pronom_question][0], qlemma_to_id[anchor][0])

        final_path_question = []
        previous_path = None
        for path in paths:
            if previous_path is None:
                previous_path = path
                continue
            try:
                final_path_question.append(qdoc_child2head_dic[previous_path][path])
            except KeyError:
                final_path_question.append(qdoc_head2child_dic[previous_path][path])

            previous_path = path

        # print(final_path_question)
        paths = nx.shortest_path(graph_answer, answer_to_anchor, alemma_to_id[anchor][0])

        final_path_answer = []
        previous_path = None
        for path in paths:
            if previous_path is None:
                previous_path = path
                continue
            try:
                final_path_answer.append(adoc_child2head_dic[previous_path][path])
            except KeyError:
                final_path_answer.append(adoc_head2child_dic[previous_path][path])

            previous_path = path

        all_edit_distances.append(editdistance.eval(final_path_question, final_path_answer))
    return np.min(all_edit_distances), lexical_variation


def get_number_paragraphs_categories(dataset_fn, by_articles=False):
    with open(dataset_fn) as f:
        dataset = json.load(f)
    titles_list = []
    categories_dic = {}
    for article in dataset:
        if article['displaytitle'] in titles_list:
            continue
        titles_list.append(article['displaytitle'])
        if article['audience'] != 'restricted':
            print(article['displaytitle'])
            continue

        if by_articles:
            to_add = 1
        else:
            to_add = len(article['paragraphs'])
        if article['categorie'] not in categories_dic:
            categories_dic[article['categorie']] = to_add
        else:
            categories_dic[article['categorie']] += to_add
    return categories_dic


def piaf_to_squad_eval(dataset_fn, restricted=True):
    with open(dataset_fn) as f:
        dataset = json.load(f)

    new_dataset = {}
    new_dataset['data'] = []
    article_list = []
    cpt = 0
    mistakes = 0
    paragraph_cpt = 0
    for article in dataset:
        new_article = {}
        if restricted:
            if article['audience'] != 'restricted':
                continue
        else:
            if article['audience'] == 'restricted':
                continue
        if article['displaytitle'] in article_list:
            continue
        article_list.append(article['displaytitle'])
        new_article['title'] = article['displaytitle']
        new_article['paragraphs'] = []

        for paragraph in article['paragraphs']:
            paragraph_cpt += 1
            new_paragraph = {}
            new_paragraph['context'] = paragraph['text']
            new_paragraph['qas'] = []
            for qa in paragraph['questions']:
                new_answers = []
                for answer in qa['answers']:
                    answer_start = new_paragraph['context'].find(answer['text'])
                    if answer_start > 0:
                        new_answers.append({'answer_start': answer_start, 'text': answer['text']})
                    else:
                        mistakes += 1
                if len(new_answers) > 0:
                    new_qa = {'question': qa['text'], 'answers': new_answers}
                    new_qa['id'] = str(cpt)
                    cpt += 1
                    new_paragraph['qas'].append(new_qa)
            if len(new_paragraph['qas']) > 0:
                new_article['paragraphs'].append(new_paragraph)
        if len(new_article['paragraphs']) > 0:
            new_dataset['data'].append(new_article)
    print(mistakes)
    print(paragraph_cpt)
    print(cpt)
    return new_dataset
