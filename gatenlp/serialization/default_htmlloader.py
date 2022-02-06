"""
Module that implements the various ways of how to save and load documents and change logs.
"""
import yaml
from gatenlp.document import Document
from gatenlp.urlfileutils import is_url, get_str_from_url
from bs4 import BeautifulSoup
import bs4


class HtmlLoader:
    """ """

    @staticmethod
    def load_rendered(
        clazz,
        from_ext=None,
        from_mem=None,
        parser=None,
        markup_set_name="Original markups",
        process_soup=None,
        offset_mapper=None,
        **kwargs,
    ):
        """

        Args:
          clazz:
          from_ext: (Default value = None)
          from_mem: (Default value = None)
          parser: (Default value = None)
          markup_set_name: (Default value = "Original markups")
          process_soup: (Default value = None)
          offset_mapper: (Default value = None)
          **kwargs:

        Returns:

        """
        raise Exception("Rendered html parser not yet implemented")

    @staticmethod
    def load(
        clazz,
        from_ext=None,
        from_mem=None,
        parser="html.parser",
        markup_set_name="Original markups",
        encoding=None,
        **kwargs,
    ):
        """Load a HTML file.

        Args:
            clazz: param from_ext:
            from_ext: file our URL source
            from_mem:  string source
            parser: one of "html.parser", "lxml", "lxml-xml", "html5lib" (default is "html.parser")
            markup_set_name: the annotation set name for the set to contain the HTML
                annotations (Default value = "Original markups")
            encoding: the encoding to use for reading the file
        """
        # NOTE: for now we have a simple heuristic for adding newlines to the text:
        # before and after a block element, a newline is added unless there is already one
        # NOTE: for now we use  multi_valued_attributes=None which prevents attributes of the
        # form "class='val1 val2'" to get converted into features with a list of values.
        isurl, extstr = is_url(from_ext)
        if from_ext is not None:
            if isurl:
                from_mem = get_str_from_url(extstr, encoding=encoding)
        if from_mem:
            bs = BeautifulSoup(from_mem, features=parser, multi_valued_attributes=None)
        else:
            with open(extstr, encoding=encoding) as infp:
                bs = BeautifulSoup(infp, features=parser, multi_valued_attributes=None)
        # we recursively iterate the tree depth first, going through the children
        # and adding to a list that either contains the text or a dict with the information
        # about annotations we want to add
        nlels = {
            "pre",
            "br",
            "p",
            "div",
            "tr",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "li",
            "address",
            "article",
            "aside",
            "blockquote",
            "del",
            "figure",
            "figcaption",
            "footer",
            "header",
            "hr",
            "ins",
            "main",
            "nav",
            "section",
            "summary",
            "input",
            "legend",
            "option",
            "textarea",
            "bdi",
            "bdo",
            "center",
            "code",
            "dfn",
            "menu",
            "dir",
            "caption",
        }
        ignoreels = {"script", "style"}
        docinfo = {"anninfos": [], "curoffset": 0, "curid": 0, "text": ""}

        def walktree(el):
            """

            Args:
              el:

            Returns:

            """
            # print("DEBUG: type=", type(el))
            if isinstance(el, bs4.element.Doctype):
                # print("DEBUG: got doctype", type(el))
                pass
            elif isinstance(el, bs4.element.Comment):
                # print("DEBUG: got Comment", type(el))
                pass
            elif isinstance(el, bs4.element.Script):
                # print("DEBUG: got Script", type(el))
                pass
            elif isinstance(el, bs4.element.Tag):
                # print("DEBUG: got tag: ", type(el), " name=",el.name)
                # some tags we ignore completely:
                if el.name in ignoreels:
                    return
                # for some tags we insert a new line before, but only if we do not already have one
                if not docinfo["text"].endswith("\n") and el.name in nlels:
                    docinfo["text"] += "\n"
                    # print("DEBUG: adding newline before at ", docinfo["curoffset"])
                    docinfo["curoffset"] += 1
                ann = {
                    "type": el.name,
                    "features": el.attrs,
                    "id": docinfo["curid"],
                    "event": "start",
                    "start": docinfo["curoffset"],
                }
                thisid = docinfo["curid"]
                docinfo["anninfos"].append(ann)
                docinfo["curid"] += 1
                for child in el.children:
                    walktree(child)
                # for some tags we insert a new line after
                if not docinfo["text"].endswith("\n") and el.name in nlels:
                    docinfo["text"] += "\n"
                    # print("DEBUG: adding newline after at ", docinfo["curoffset"])
                    docinfo["curoffset"] += 1
                docinfo["anninfos"].append(
                    {"event": "end", "id": thisid, "end": docinfo["curoffset"]}
                )
            elif isinstance(el, bs4.element.NavigableString):
                # print("DEBUG: got text: ", el)
                text = str(el)
                if text == "\n" and docinfo["text"].endswith("\n"):
                    return
                docinfo["text"] += text
                docinfo["curoffset"] += len(el)
            else:
                print("WARNING: odd element type", type(el))

        walktree(bs)
        # need to add the end corresponding to bs
        # print("DEBUG: got docinfo:\n",docinfo)
        id2anninfo = {}  # from id to anninfo
        nstart = 0
        for anninfo in docinfo["anninfos"]:
            if anninfo["event"] == "start":
                nstart += 1
                id2anninfo[anninfo["id"]] = anninfo
        nend = 0
        for anninfo in docinfo["anninfos"]:
            if anninfo["event"] == "end":
                nend += 1
                end = anninfo["end"]
                annid = anninfo["id"]
                anninfo = id2anninfo[annid]
                anninfo["end"] = end
        # print("DEBUG: got nstart/nend", nstart, nend)
        assert nstart == nend
        # print("DEBUG: got id2anninfo:\n", id2anninfo)
        doc = Document(docinfo["text"])
        annset = doc.annset(markup_set_name)
        for i in range(nstart):
            anninfo = id2anninfo[i]
            annset.add(
                anninfo["start"],
                anninfo["end"],
                anntype=anninfo["type"],
                features=anninfo["features"],
            )
        return doc

