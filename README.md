# PIAF Data Generation and Analysis
PIAF (Pour une IA Francophone)  is a French project carried on by [Etalab](https://etalab.gouv.fr) (the French's government open data task force) in the context of its Lab IA.
PIAF's goal is to build a natively French SQuAD like Question Answering dataset. We do this by leveraging the community to create
question-answers pairs with the help of our [annotation platform](https://github.com/etalab/piaf).

This annotation platform begins with a subsample of the French Wikipedia, as described [here](https://piaf.etalab.studio/protocole-fr/).

This repo contains the code created by our partner [ReciTAL](https://recital.ai) used to generate this subsample and to compute lexical and syntactical statistics on the
collected data. All this can be found in the protocol, linked above.

To generate a subsample, such as the one used, please follow these instructions:

### 0. Install requirements 
Python: 
* ```conda env create -f environment.yml```

spaCy:
* Install the spaCy French model:
```python -m spacy download fr_core_news_sm```

### 1. Download a French Wikipedia dump (only page and pagelinks.sql.gz are required)

For example, the dumps from 2020/01/20 links are:
* https://dumps.wikimedia.org/frwiki/20200120/frwiki-20200120-page.sql.gz
* https://dumps.wikimedia.org/frwiki/20200120/frwiki-20200120-pagelinks.sql.gz

These dumps are removed periodically, you can find the current dumps at https://dumps.wikimedia.org/frwiki

### 2. Compile and launch the PageRank scorer (by [nayuki](https://www.nayuki.io/page/computing-wikipedias-internal-pageranks)) ```WikipediaPagerank.java```
This will perform 1000 iterations of PageRank and save the output in three files. You will need a recent JDK installed in your machine.

```bash
javac WikipediaPagerank.java
java -Xmx8G WikipediaPagerank frwiki-20190920-page.sql.gz frwiki-20190920-pagelinks.sql.gz 1000
```

The program outputs three .raw files:

* ```wikipedia-pageranks.raw```
* ```wikipedia-pagerank-page-links.raw```
* ```wikipedia-pagerank-page-id-title.raw```

### 3. Launch ```dump_topn.py``` to select the top N (here N = 10000) articles based on the computed PageRank score:
```bash
python dump_topn.py 10000 wikipedia-pageranks.raw wikipedia-pagerank-page-id-title.raw output_path_wikipedia-pagerank-title.txt
```

The program outputs a single file: ```topN.pkl```. Inside ```wiki-preparation/data``` we share a ```top25k.pkl``` with our top 25k articles from French Wikipedia.

### 4. Launch ```dump.py``` to query Wikipedia and obtain the actual content of the Wikipedia articles:
```bash
python dump.py topN.pkl
```

The program outputs two folders:
* ```data/Nhtml```: The content of N Wikipedia articles in HTML format
* ```data/Npages```: The content of N Wikipedia articles in WIKI format

### 5. Launch ```compute_wiki_stats.py``` to calculate the statistics of each article such as text length, paragraph length, and so on.
```bash
python compute_wiki_stats.py --folder_path data/Npages --html_path data/Nhtml --output_dic_fn stats_topN.pkl
``` 

The program outputs a single file with the statistics: stats_topN.pkl

### 6. Launch ```stats_analysis_results.py``` to filter filter the articles into a json file
```bash
python stats_analysis_results.py --pkl_stats_dic_fn stats_topN.pkl --wiki_path data/Npages --html_path Nhtml --output_json_article_fn articles.json --min_paragraphs 5 --min_len_paragraphs 500 --max_len_paragraphs 1000 
```

The program outputs the file ```articles.json``` which is a SQuAD compatible JSON file ready to be used by the PIAF Annotation tool.

### 7. Launch qas-analysis/divergence to compute the syntactic and lexical metrics on the recollected data
```bash
python qas-analysis/divergence.py piaf-annotations_v1.1.json
```

This program outputs two PDF files:
* hits_syntaxic.pdf: with the sytactic analysis of the PIAF dataset
* lexical_variation_piaf_by_tokens_lemma.pdf: with the lexical analysis

### And now, a beautiful diagram of the whole procedure:
![piaf_code](https://user-images.githubusercontent.com/1085210/73561370-27478c80-4459-11ea-80cb-7a0dd4655deb.png)
