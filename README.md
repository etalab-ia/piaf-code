

## 0. Install requirements 
Python: 
* From ```requirements.pyl``` or ```requirements.txt```.

spaCY:
* Install spaCy French model:
```python -m spacy download fr_core_news_sm```

## 1. Download a French Wikipedia dump (only page and pagelinks.sql.gz are required)

For example, the dumps from 2019/09/20 links are:
* https://dumps.wikimedia.org/frwiki/20200120/frwiki-20200120-page.sql.gz
* https://dumps.wikimedia.org/frwiki/20200120/frwiki-20200120-pagelinks.sql.gz

These dumps are removed periodically, you can find the current dumps at https://dumps.wikimedia.org/frwiki

## 2. Compile and launch the PageRank scorer (najuki's code) ```WikipediaPagerank.java```
This will perform 1000 iterations of PageRank and save the output in three files. You will need a recent JDK installed in your machine.

```shell
javac WikipediaPagerank.java
java -Xmx8G WikipediaPagerank frwiki-20190920-page.sql.gz frwiki-20190920-pagelinks.sql.gz 1000
```

The program outputs three .raw files:

* ```wikipedia-pageranks.raw```
* ```wikipedia-pagerank-page-links.raw```
* ```wikipedia-pagerank-page-id-title.raw```

## 3. Launch ```dump_topn.py``` to select the top N (here N = 10000) articles based on the computed PageRank score:
```python
python dump_topn.py 10000 wikipedia-pageranks.raw wikipedia-pagerank-page-id-title.raw output_path_wikipedia-pagerank-title.txt
```

The program outputs a single file: ```topN.pkl```. Inside ```wiki-preparation/data``` we share a ```top25k.pkl``` with our top 25k articles from French Wikipedia.

## 4. Launch ```dump.py``` to query Wikipedia and obtain the actual content of the Wikipedia articles:
```python
python dump.py topN.pkl
```

The program outputs two folders:
* ```data/Nhtml```: The content of N Wikipedia articles in HTML format
* ```data/Npages```: The content of N Wikipedia articles in WIKI format

## 5. Launch ```compute_wiki_stats.py``` to calculate the statistics of each article such as text length, paragraph length, and so on.
```python
python compute_wiki_stats.py --folder_path data/Npages --html_path data/Nhtml --output_dic_fn stats_topN.pkl
``` 

The program outputs a single file with the statistics: stats_topN.pkl

## 6. Launch ```stats_analysis_results.py``` to filter filter the articles into a json file
```python
python stats_analysis_results.py --pkl_stats_dic_fn stats_topN.pkl --wiki_path data/Npages --html_path Nhtml --output_json_article_fn articles.json --min_paragraphs 5 --min_len_paragraphs 500 --max_len_paragraphs 1000 
```

The program outputs the file ```articles.json``` which is a SQuAD compatible JSON file ready to be used by the PIAF Annotation tool.

## 7. Launch qas-analysis/divergence to compute the syntactic and lexical metrics on the recollected data
```python
python qas-analysis/divergence.py piaf-annotations_v1.1.json
```

This program outputs two PDF files:
* hits_syntaxic.pdf: with the sytactic analysis of the PIAF dataset
* lexical_variation_piaf_by_tokens_lemma.pdf: with the lexical analysis