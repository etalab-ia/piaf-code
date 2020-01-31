import struct
import pickle
import sys


class DataInputStream:
    """
    Reading from Java DataInputStream format.
    """

    def __init__(self, stream):
        self.stream = stream

    def read_boolean(self):
        return struct.unpack('?', self.stream.read(1))[0]

    def read_byte(self):
        return struct.unpack('b', self.stream.read(1))[0]

    def read_unsigned_byte(self):
        return struct.unpack('B', self.stream.read(1))[0]

    def read_char(self):
        return chr(struct.unpack('>H', self.stream.read(2))[0])

    def read_double(self):
        return struct.unpack('>d', self.stream.read(8))[0]

    def read_float(self):
        return struct.unpack('>f', self.stream.read(4))[0]

    def read_short(self):
        return struct.unpack('>h', self.stream.read(2))[0]

    def read_unsigned_short(self):
        return struct.unpack('>H', self.stream.read(2))[0]

    def read_long(self):
        return struct.unpack('>q', self.stream.read(8))[0]

    def read_utf(self):
        utf_length = struct.unpack('>H', self.stream.read(2))[0]
        return self.stream.read(utf_length)

    def read_int(self):
        return struct.unpack('>i', self.stream.read(4))[0]


def main(top_n, path_wiki_pageranks_raw, path_wiki_pagerank_id_title_raw, path_wiki_pagerank_title):
    pageranks = []

    with open(path_wiki_pageranks_raw, 'rb') as f:
        stream = DataInputStream(f)
        while True:
            try:
                val = stream.read_double()
                pageranks.append(val)
            except struct.error:
                print("I am dead")
                break

    id_title = {}

    with open(path_wiki_pagerank_id_title_raw) as f:
        for title in f:
            page_id = int(f.readline())
            id_title[page_id] = title.rstrip()

    with open(path_wiki_pagerank_title, 'w') as f:
        for page_id, pagerank in enumerate(pageranks):
            if pagerank > 0.0 and page_id in id_title:
                title = id_title.get(page_id)
                f.write('{} \t {} \n '.format(pagerank, title))

    with open(path_wiki_pagerank_title) as f:
        tuples = [(i.split('\t')[0], i.split('\t')[1])
                  for i in f.readlines() if i.strip()]

    sorted_ = sorted(tuples, key=lambda tup: tup[0])

    pickle.dump(sorted_[:top_n], open(f"top_{top_n}.pkl", 'wb'))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: \n dump_topn.py top_N input_path_wikipedia-pageranks.raw"
            " input_path_wikipedia-pagerank-id-title.raw"
            " output_path_wikipedia-pagerank-title.txt")
        exit(1)

    top_n = int(sys.argv[1])
    path_wiki_pageranks_raw = sys.argv[2]
    path_wiki_pagerank_id_title_raw = sys.argv[3]
    path_wiki_pagerank_title = sys.argv[4]

    main(top_n, path_wiki_pageranks_raw,
         path_wiki_pagerank_id_title_raw,
         path_wiki_pagerank_title)
