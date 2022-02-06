"""
Module that implements the various ways of how to save and load documents and change logs.
"""
from gatenlp.document import Document
from gatenlp.urlfileutils import is_url, get_str_from_url, get_bytes_from_url
from gzip import open as gopen, compress, decompress


class PlainTextSerializer:
    """ """

    @staticmethod
    def save(
        clazz,
        inst,
        to_ext=None,
        to_mem=None,
        offset_type=None,
        offset_mapper=None,
        encoding="UTF-8",
        gzip=False,
        **kwargs,
    ):
        """

        Args:
          clazz:
          inst:
          to_ext: (Default value = None)
          to_mem: (Default value = None)
          offset_type: (Default value = None)
          offset_mapper: (Default value = None)
          encoding: (Default value = "UTF-8")
          gzip: (Default value = False)
          **kwargs:

        Returns:

        """
        txt = inst.text
        if txt is None:
            txt = ""
        if to_mem:
            if gzip:
                compress(txt.encode(encoding))
            else:
                return txt
        else:
            if gzip:
                with gopen(to_ext, "wt", encoding=encoding) as outfp:
                    outfp.write(txt)
            else:
                with open(to_ext, "wt", encoding=encoding) as outfp:
                    outfp.write(txt)

    @staticmethod
    def save_gzip(clazz, inst, **kwargs):
        """

        Args:
          clazz:
          inst:
          **kwargs:

        Returns:

        """
        PlainTextSerializer.save(clazz, inst, gzip=True, **kwargs)

    @staticmethod
    def load(
        clazz,
        from_ext=None,
        from_mem=None,
        offset_mapper=None,
        encoding="UTF-8",
        gzip=False,
        **kwargs,
    ):
        """

        Args:
          clazz:
          from_ext: (Default value = None)
          from_mem: (Default value = None)
          offset_mapper: (Default value = None)
          encoding: (Default value = "UTF-8")
          gzip: (Default value = False)
          **kwargs:

        Returns:

        """
        isurl, extstr = is_url(from_ext)
        if from_ext is not None:
            if isurl:
                if gzip:
                    from_mem = get_bytes_from_url(extstr)
                else:
                    from_mem = get_str_from_url(extstr, encoding=encoding)
        if from_mem is not None:
            if gzip:
                txt = decompress(from_mem).decode(encoding)
            else:
                txt = from_mem
            doc = Document(txt)
        else:
            if gzip:
                with gopen(extstr, "rt", encoding=encoding) as infp:
                    txt = infp.read()
            else:
                with open(extstr, "rt", encoding=encoding) as infp:
                    txt = infp.read()
            doc = Document(txt)
        return doc

    @staticmethod
    def load_gzip(clazz, **kwargs):
        """

        Args:
          clazz:
          **kwargs:

        Returns:

        """
        return PlainTextSerializer.load(clazz, gzip=True, **kwargs)
