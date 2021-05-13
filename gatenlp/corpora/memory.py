"""
Module that defines Corpus and DocumentSource/DocumentDestination classes which access documents
from in-memory objects.
"""


from gatenlp import Document
from gatenlp.corpora.base import DocumentSource, Corpus


class ListCorpus(Corpus):
    """
    Make a Python list of documents available as a Corpus instance.
    """
    @classmethod
    def empty(cls, n):
        """
        Create an empty corpus of size n where all elements are None.

        Args:
            n: size of corpus

        Returns:
            a ListCorpus instance with n elements which are all None
        """
        l1 = [None] * n
        return cls(l1)

    def __init__(self, thelist, store_none=True):
        """
        Provides a corpus interface to a list or list-like data structure.
        Note that this provides the proper implementation of append which stores back to the index
        provided in the document feature "__idx" instead of actually appending a new element to the list!

        Args:
            thelist: the list to wrap as a corpus
            store_none: if True, a None value is stored into the corpus, otherwise, None will leave the
                entry unchanged.
        """
        super().__init__()
        self._list = thelist
        self.store_none = store_none

    def __getitem__(self, idx):
        doc = self._list[idx]
        self.setidxfeature(doc, idx)
        return doc

    def __setitem__(self, key, value):
        if value is None:
            if self.store_none:
                self._list[key] = value
        else:
            assert isinstance(value, Document)
            self._list[key] = value

    def __len__(self):
        return len(self._list)

    def append(self, doc: Document):
        if doc is None:
            if self.store_none:
                self._list.append(doc)
        else:
            assert isinstance(doc, Document)
            self._list.append(doc)


# TODO: implement data_cols
class PandasDfSource(DocumentSource):
    """
    A document source which creates documents from the text in some data frame column for each row, and
    sets features from arbitrary columns in the row.
    """

    def __init__(self, df, text_col=None, feature_cols=None, data_cols=None, data_feature="__data"):
        """
        Creates a PandasDfSource.

        Args:
            df: the data frae
            text_col:  the name of the column that contains the text
            feature_cols: a dictionary that maps document feature names to column names of where to get the
               feature value from (default: None)
            data_cols: if a list, store those cols in the data feature, if True, store all cols.
            data_feature: the name of the data feature, default is "__data"
        """
        assert text_col is not None
        self.text_col = text_col
        self.feature_cols = feature_cols
        self.source = df
        self.reader = df.iterrows()
        self.n = 0
        self.data_cols = data_cols
        self.data_feature = data_feature
        self.colnames = list(df.columns)

    def __iter__(self):
        for _, row in self.reader:
            text = row[self.text_col]
            doc = Document(text)
            if self.feature_cols:
                for fname, colname in self.feature_cols.items():
                    value = row[colname]
                    doc.features[fname] = value
            if self.data_cols:
                if isinstance(self.data_cols, list):
                    data = {}
                    for cname in self.data_cols:
                        data[cname] = row[cname]
                else:
                    data = {fname: row[fname] for fname in self.colnames}
                doc.features[self.data_feature] = data
            self.n += 1
            yield doc
