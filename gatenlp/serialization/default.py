"""
Module that implements the various ways of how to save and load documents and change logs.
"""
import io
import os
import sys
import yaml

# import ruyaml as yaml
try:
    from yaml import CFullLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import FullLoader as Loader, Dumper
yaml_loader = yaml.Loader
yaml_dumper = yaml.Dumper
from random import choice
from string import ascii_uppercase
from msgpack import pack, Unpacker
from gatenlp.document import Document
from gatenlp.annotation_set import AnnotationSet
from gatenlp.annotation import Annotation
from gatenlp.changelog import ChangeLog
from gatenlp.features import Features
from gatenlp.utils import get_nested
from gatenlp.urlfileutils import is_url, get_str_from_url, get_bytes_from_url
from gzip import open as gopen, compress, decompress
from bs4 import BeautifulSoup
from gatenlp.gatenlpconfig import gatenlpconfig
import bs4
import warnings
import pickle

try:
    from bs4 import GuessedAtParserWarning
    warnings.filterwarnings("ignore", category=GuessedAtParserWarning)
except Exception as ex:
    pass


# import orjson as usejson
# import json as usejson
# import rapidjson as usejson
# import ujson as usejson
# import hyperjson as usejson
import json

JSON_WRITE = "wt"
JSON_READ = "rt"

# # for replacing json by orjson
# class json:
#     @staticmethod
#     def load(fp):
#         data = fp.read()
#         return usejson.loads(data)
#     @staticmethod
#     def loads(data):
#         return usejson.loads(data)
#     @staticmethod
#     def dump(obj, fp):
#         buf = usejson.dumps(obj)
#         fp.write(buf)
#     @staticmethod
#     def dumps(obj):
#         return usejson.dumps(obj)

# # for replacing json with one of the other implementations
# class json:
#     @staticmethod
#     def load(fp):
#         return usejson.load(fp)
#     @staticmethod
#     def loads(data):
#         return usejson.loads(data)
#     @staticmethod
#     def dump(obj, fp):
#         buf = usejson.dump(obj, fp)
#     @staticmethod
#     def dumps(obj):
#         return usejson.dumps(obj)


# TODO: for ALL save options, allow to filter the annotations that get saved!
# TODO: then use this show only limited set of annotations in the viewer
# TODO: create Document.display(....) to show document in various ways in the current
#   environment, e.g. Jupyter notebook, select anns, configure colour palette, size etc.


# TODO: when loading from a URL, allow for deciding on the format based on the mime type!
# So if we do not have the format, we should get the header for the file, check the mime type and see
# if  we have a loder registered for that and then let the loader do the rest of the work. This may
# need loaders to be able to use an already open stream.

TWITTER_DEFAULT_INCLUDE_FIELDS = [
    "id_str",
    "user.id_str",
    "user.screen_name",
    "user.name" "created_at",
    "is_quote_status",
    "quote_count",
    "retweet_count",
    "favourite_count",
    "favourited",
    "retweeted",
    "lang",
    "$is_retweet_status",
    "retweeted_status.user.screen_name",
]


class JsonSerializer:
    """
    This class performs the saving and load of Documents and ChangeLog instances to and from the
    BDOC JSON format files, optionally with gzip compression.
    """

    @staticmethod
    def save(
        clazz,
        inst,
        to_ext=None,
        to_mem=None,
        offset_type=None,
        offset_mapper=None,
        gzip=False,
        annsets=None,
        **kwargs,
    ):
        """

        Args:
          clazz: the class of the object that gets saved
          inst: the object to get saved
          to_ext: where to save to, this should be a file path, only one of to_ext and to_mem should be specified
          to_mem: if True, return a String serialization
          offset_type: the offset type to use for saving, if None (default) use "p" (Python)
          offset_mapper: the offset mapper to use, only needed if the type needs to get converted
          gzip: if True, the JSON gets gzip compressed
          annsets: which annotation sets and types to include, list of set names or (setanmes, types) tuples
          **kwargs:
        """
        d = inst.to_dict(offset_type=offset_type, offset_mapper=offset_mapper, annsets=annsets, **kwargs)
        if to_mem:
            if gzip:
                compress(json.dumps(d).encode("UTF-8"))
            else:
                return json.dumps(d)
        else:
            if gzip:
                with gopen(to_ext, JSON_WRITE) as outfp:
                    json.dump(d, outfp)
            else:
                with open(to_ext, JSON_WRITE) as outfp:
                    json.dump(d, outfp)

    @staticmethod
    def save_gzip(clazz, inst, **kwargs):
        """
        Invokes the save method with gzip=True
        """
        JsonSerializer.save(clazz, inst, gzip=True, **kwargs)

    @staticmethod
    def load(
        clazz, from_ext=None, from_mem=None, offset_mapper=None, gzip=False, **kwargs
    ):
        """

        Args:
          clazz:
          from_ext: (Default value = None)
          from_mem: (Default value = None)
          offset_mapper: (Default value = None)
          gzip: (Default value = False)
          **kwargs:

        Returns:

        """
        # print("RUNNING load with from_ext=", from_ext, " from_mem=", from_mem)

        if from_ext is not None and from_mem is not None:
            raise Exception("Exactly one of from_ext and from_mem must be specified ")
        if from_ext is None and from_mem is None:
            raise Exception("Exactly one of from_ext and from_mem must be specified ")

        isurl, extstr = is_url(from_ext)
        if from_ext is not None:
            if isurl:
                # print("DEBUG: we got a URL")
                if gzip:
                    from_mem = get_bytes_from_url(extstr)
                else:
                    from_mem = get_str_from_url(extstr, encoding="utf-8")
            else:
                # print("DEBUG: not a URL !!!")
                pass
        if from_mem is not None:
            if gzip:
                d = json.loads(decompress(from_mem).decode("UTF-8"))
            else:
                d = json.loads(from_mem)
            doc = clazz.from_dict(d, offset_mapper=offset_mapper, **kwargs)
        else:  # from_ext must have been not None and a path
            if gzip:
                with gopen(extstr, JSON_READ) as infp:
                    d = json.load(infp)
            else:
                with open(extstr, JSON_READ) as infp:
                    d = json.load(infp)
            doc = clazz.from_dict(d, offset_mapper=offset_mapper, **kwargs)
        return doc

    @staticmethod
    def load_gzip(clazz, **kwargs):
        """

        Args:
          clazz:
          **kwargs:

        Returns:

        """
        return JsonSerializer.load(clazz, gzip=True, **kwargs)


class PickleSerializer:
    """
    This class performs the saving and load of Documents and ChangeLog instances to and from pickle format.
    """

    @staticmethod
    def save(
        clazz,
        inst,
        to_ext=None,
        to_mem=None,
        offset_type=None,
        offset_mapper=None,
        gzip=False,
        **kwargs,
    ):
        """

        Args:
          clazz: the class of the object that gets saved
          inst: the object to get saved
          to_ext: where to save to, this should be a file path, only one of to_ext and to_mem should be specified
          to_mem: if True, return a String serialization
          offset_type: the offset type to use for saving, if None (default) use "p" (Python)
          offset_mapper: the offset mapper to use, only needed if the type needs to get converted
          gzip: must be False, gzip is not supported
          **kwargs:
        """
        if gzip:
            raise Exception("Gzip not supported for pickle")
        if to_mem:
            return pickle.dumps(inst, protocol=-1)
        else:
            with open(to_ext, "wb") as outfp:
                pickle.dump(inst, outfp, protocol=-1)

    @staticmethod
    def load(
        clazz, from_ext=None, from_mem=None, offset_mapper=None, gzip=False, **kwargs
    ):
        """

        Args:
          clazz:
          from_ext: (Default value = None)
          from_mem: (Default value = None)
          offset_mapper: (Default value = None)
          gzip: (Default value = False) must be False, True not supported
          **kwargs:

        Returns:

        """
        # print("RUNNING load with from_ext=", from_ext, " from_mem=", from_mem)

        if from_ext is not None and from_mem is not None:
            raise Exception("Exactly one of from_ext and from_mem must be specified ")
        if from_ext is None and from_mem is None:
            raise Exception("Exactly one of from_ext and from_mem must be specified ")

        isurl, extstr = is_url(from_ext)
        if from_ext is not None:
            if isurl:
                from_mem = get_bytes_from_url(extstr)
            else:
                # print("DEBUG: not a URL !!!")
                pass
        if from_mem is not None:
            doc = pickle.loads(from_mem)
        else:  # from_ext must have been not None and a path
            with open(extstr, "rb") as infp:
                doc = pickle.load(infp)
        return doc


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


class YamlSerializer:
    """ """

    @staticmethod
    def save(
        clazz,
        inst,
        to_ext=None,
        to_mem=None,
        offset_type=None,
        offset_mapper=None,
        gzip=False,
        annsets=None,
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
            gzip: (Default value = False)
            annsets: which annotation sets and types to include, list of set names or (setanmes, types) tuples
            **kwargs:
        """
        d = inst.to_dict(offset_type=offset_type, offset_mapper=offset_mapper, annsets=annsets, **kwargs)
        if to_mem:
            if gzip:
                compress(yaml.dump(d, Dumper=yaml_dumper).encode("UTF-8"))
            else:
                return yaml.dump(d, Dumper=yaml_dumper)
        else:
            if gzip:
                with gopen(to_ext, "wt") as outfp:
                    yaml.dump(d, outfp, Dumper=yaml_dumper)
            else:
                with open(to_ext, "wt") as outfp:
                    yaml.dump(d, outfp, Dumper=yaml_dumper)

    @staticmethod
    def save_gzip(clazz, inst, **kwargs):
        """

        Args:
          clazz:
          inst:
          **kwargs:

        Returns:

        """
        YamlSerializer.save(clazz, inst, gzip=True, **kwargs)

    @staticmethod
    def load(
        clazz, from_ext=None, from_mem=None, offset_mapper=None, gzip=False, **kwargs
    ):
        """

        Args:
          clazz:
          from_ext: (Default value = None)
          from_mem: (Default value = None)
          offset_mapper: (Default value = None)
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
                    from_mem = get_str_from_url(extstr, encoding="utf-8")
        if from_mem is not None:
            if gzip:
                d = yaml.load(decompress(from_mem).decode("UTF-8"), Loader=yaml_loader)
            else:
                d = yaml.load(from_mem, Loader=yaml_loader)
            doc = clazz.from_dict(d, offset_mapper=offset_mapper, **kwargs)
        else:
            if gzip:
                with gopen(extstr, "rt") as infp:
                    d = yaml.load(infp, Loader=yaml_loader)
            else:
                with open(extstr, "rt") as infp:
                    d = yaml.load(infp, Loader=yaml_loader)
            doc = clazz.from_dict(d, offset_mapper=offset_mapper, **kwargs)
        return doc

    @staticmethod
    def load_gzip(clazz, **kwargs):
        """

        Args:
          clazz:
          **kwargs:

        Returns:

        """
        return YamlSerializer.load(clazz, gzip=True, **kwargs)


MSGPACK_VERSION_HDR = "sm2"


class MsgPackSerializer:
    """ """

    @staticmethod
    def document2stream(doc: Document, stream):
        """

        Args:
          doc: Document:
          stream:
          doc: Document:

        Returns:

        """
        pack(MSGPACK_VERSION_HDR, stream)
        pack(doc.offset_type, stream)
        pack(doc.text, stream)
        pack(doc.name, stream)
        pack(doc._features.to_dict(), stream)
        pack(len(doc._annotation_sets), stream)
        for name, annset in doc._annotation_sets.items():
            pack(name, stream)
            pack(annset._next_annid, stream)
            pack(len(annset), stream)
            for ann in annset.fast_iter():
                pack(ann.type, stream)
                pack(ann.start, stream)
                pack(ann.end, stream)
                pack(ann.id, stream)
                pack(ann.features.to_dict(), stream)

    @staticmethod
    def stream2document(stream):
        """

        Args:
          stream:

        Returns:

        """
        u = Unpacker(stream)
        version = u.unpack()
        if version != MSGPACK_VERSION_HDR:
            raise Exception("MsgPack data starts with wrong version")
        doc = Document()
        doc.offset_type = u.unpack()
        doc._text = u.unpack()
        doc.name = u.unpack()
        doc._features = Features(u.unpack())
        nsets = u.unpack()
        setsdict = dict()
        doc.annotation_sets = setsdict
        for iset in range(nsets):
            sname = u.unpack()
            if sname is None:
                sname = ""
            annset = AnnotationSet(name=sname, owner_doc=doc)
            annset._next_annid = u.unpack()
            nanns = u.unpack()
            for iann in range(nanns):
                atype = u.unpack()
                astart = u.unpack()
                aend = u.unpack()
                aid = u.unpack()
                afeatures = u.unpack()
                ann = Annotation(astart, aend, atype, annid=aid, features=afeatures)
                annset._annotations[aid] = ann
            setsdict[sname] = annset
        doc._annotation_sets = setsdict
        return doc

    @staticmethod
    def save(
        clazz,
        inst,
        to_ext=None,
        to_mem=None,
        offset_type=None,
        offset_mapper=None,
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
          **kwargs:

        Returns:

        """
        if isinstance(inst, Document):
            writer = MsgPackSerializer.document2stream
        elif isinstance(inst, ChangeLog):
            raise Exception("Not implemented yet")
        else:
            raise Exception("Object not supported")
        if to_mem:
            f = io.BytesIO()
        else:
            f = open(to_ext, "wb")
        writer(inst, f)
        if to_mem:
            return f.getvalue()
        else:
            f.close()

    @staticmethod
    def load(clazz, from_ext=None, from_mem=None, offset_mapper=None, **kwargs):
        """

        Args:
          clazz:
          from_ext: (Default value = None)
          from_mem: (Default value = None)
          offset_mapper: (Default value = None)
          **kwargs:

        Returns:

        """
        if clazz == Document:
            reader = MsgPackSerializer.stream2document
        elif clazz == ChangeLog:
            raise Exception("Not implemented yet")
        else:
            raise Exception("Object not supported")

        isurl, extstr = is_url(from_ext)
        if from_ext is not None:
            if isurl:
                from_mem = get_bytes_from_url(extstr)
        if from_mem:
            f = io.BytesIO(from_mem)
        else:
            f = open(extstr, "rb")
        doc = reader(f)
        return doc


JS_JQUERY = '<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>'
JS_GATENLP = '<script src="https://unpkg.com/gatenlp-ann-viewer@1.0.12/gatenlp-ann-viewer.js"></script>'
HTML_TEMPLATE_FILE_NAME = "gatenlp-ann-viewer.html"
JS_GATENLP_FILE_NAME = "gatenlp-ann-viewer-merged.js"

html_ann_viewer_serializer_js_loaded = False


class HtmlAnnViewerSerializer:
    """ """

    @staticmethod
    def javascript():
        """
        Return the Javascript needed for the HTML Annotation viewer.

        Returns: Javascript string.

        """
        jsloc = os.path.join(
            os.path.dirname(__file__), "_htmlviewer", JS_GATENLP_FILE_NAME
        )
        if not os.path.exists(jsloc):
            raise Exception(
                "Could not find JavsScript file, {} does not exist".format(jsloc)
            )
        with open(jsloc, "rt", encoding="utf-8") as infp:
            js = infp.read()
            js = """<script type="text/javascript">""" + js + "</script>"
        return js

    @staticmethod
    def init_javscript():
        import IPython

        IPython.display.display_html(HtmlAnnViewerSerializer.javascript(), raw=True)

    @staticmethod
    def save(
        clazz,
        inst,
        to_ext=None,
        to_mem=None,
        notebook=False,
        offline=False,
        add_js=True,
        htmlid=None,
        stretch_height=False,
        annsets=None,
        doc_style=None,
        **kwargs,
    ):
        """Convert a document to HTML for visualizing it.

        Args:
            clazz: the class of the object to save
            inst: the instance/object to save
            to_ext:  the destination where to save to unless to_mem is given
            to_mem: if true, ignores to_ext and returns the representation
            notebook: if True only create a div which can be injected into a notebook or other HTML, otherwise
                generate a full HTML document
            offline: if true, include all the Javascript needed in the generated HTML , otherwise load library
                from the internet.
            add_js: if true (default), add the necessary Javascript either directly or by loading a library from
                the internet. If false, assume that the Javascript is already there (only makes sense with
                notebook=True).
            htmlid: the id to use for HTML ids so it is possible to have several independent viewers in the
                same HTML page and to style the output from a separate notebook cell
            max_height1: if this is set, then the maximum height of the first row of the viewer is set to the
                given value (default: 20em). If this is None, then the height is set to
            stretch_height: if False, rows 1 and 2 of the viewer will not have the height set, but only
                min and max height (default min is 10em for row1 and 7em for row2, max is the double of those).
                If True, no max haight is set and instead the height is set to a percentage (default is
                67vh for row 1 and 30vh for row 2). The values used can be changed via gateconfig.
            annsets: if None, include all annotation sets and types, otherwise this should be a list of either
                set names, or tuples, where the first entry is a set name and the second entry is either a type
                name or list of type names to include.
            doc_style: if not None, any additional styling for the document text box, if None, use whatever
                is defined in gatenlpconfig or do not use.
            kwargs: swallow any other kwargs.

        Returns: if to_mem is True, returns the representation, otherwise None.

        """
        if not isinstance(inst, Document):
            raise Exception("Not a document!")
        # TODO: why are we doing a deepcopy here?
        doccopy = inst.deepcopy(annsets=annsets)
        doccopy.to_offset_type("j")
        json = doccopy.save_mem(fmt="json", **kwargs)
        htmlloc = os.path.join(
            os.path.dirname(__file__), "_htmlviewer", HTML_TEMPLATE_FILE_NAME
        )
        if not os.path.exists(htmlloc):
            raise Exception(
                "Could not find HTML template, {} does not exist".format(htmlloc)
            )
        with open(htmlloc, "rt", encoding="utf-8") as infp:
            html = infp.read()
        txtcolor = gatenlpconfig.doc_html_repr_txtcolor
        if notebook:
            str_start = "<!--STARTDIV-->"
            str_end = "<!--ENDDIV-->"
            idx1 = html.find(str_start) + len(str_start)
            idx2 = html.find(str_end)
            if htmlid:
                rndpref = str(htmlid)
            else:
                rndpref = "".join(choice(ascii_uppercase) for i in range(10))
            html = html[idx1:idx2]
            html = f"""<div><style>#{rndpref}-wrapper {{ color: {txtcolor} !important; }}</style>
<div id="{rndpref}-wrapper">
{html}
</div></div>"""
            # replace the prefix with a random one
            html = html.replace("GATENLPID", rndpref)
        if offline:
            # global html_ann_viewer_serializer_js_loaded
            # if not html_ann_viewer_serializer_js_loaded:
            if add_js:
                jsloc = os.path.join(
                    os.path.dirname(__file__), "_htmlviewer", JS_GATENLP_FILE_NAME
                )
                if not os.path.exists(jsloc):
                    raise Exception(
                        "Could not find JavsScript file, {} does not exist".format(
                            jsloc
                        )
                    )
                with open(jsloc, "rt", encoding="utf-8") as infp:
                    js = infp.read()
                    js = """<script type="text/javascript">""" + js + "</script>"
                # html_ann_viewer_serializer_js_loaded = True
            else:
                js = ""
        else:
            js = JS_JQUERY + JS_GATENLP
        if stretch_height:
            height1 = gatenlpconfig.doc_html_repr_height1_stretch
            height2 = gatenlpconfig.doc_html_repr_height2_stretch
        else:
            height1 = gatenlpconfig.doc_html_repr_height1_nostretch
            height2 = gatenlpconfig.doc_html_repr_height2_nostretch
        html = html.replace("$$JAVASCRIPT$$", js, 1).replace("$$JSONDATA$$", json, 1)
        html = html.replace("$$HEIGHT1$$", height1, 1).replace(
            "$$HEIGHT2$$", height2, 1
        )
        if doc_style is None:
            doc_style = gatenlpconfig.doc_html_repr_doc_style
        if doc_style is None:
            doc_style = ""
        html = html.replace("$$DOCTEXTSTYLE$$", doc_style, 1)
        if to_mem:
            return html
        else:
            with open(to_ext, "wt", encoding="utf-8") as outfp:
                outfp.write(html)


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


class TweetLoader:
    @staticmethod
    def load(
        clazz,
        from_ext=None,
        from_mem=None,
        include_fields=None,
        include_entities=True,
        include_quote=False,
        outsetname="Original markups",
        tweet_ann="Tweet",
    ):
        """
        Load a tweet from Twitter JSON format.

        IMPORTANT: this is still very experimental, will change in the future!

        Args:
            clazz: internal use
            from_ext: the file/url to load from
            from_mem: string to load from
            include_fields: a list of fields to include where nested field names are dot-separated, e.g.
               "user.location". All these fields are included using the nested field name in either the
               features of the tweet annotation with the Type specified, or the features of the document
               if `tweet_ann` is None.
            include_entities: create annotations for the tweet entities in the set with outsetname
            include_quote: if True, add the quoted tweet after an empty line and treat it as a separate
               tweet just like the original tweet.
            outset: the annotation set where to put entity annotations and the tweet annotation(s)
            tweet_ann: the annotation type to use to span the tweet and contain all the features.

        Returns:
            document representing the tweet
        """
        if from_ext is not None:
            isurl, extstr = is_url(from_ext)
            if isurl:
                jsonstr = get_str_from_url(extstr, encoding="utf-8")
                tweet = json.loads(jsonstr)
            else:
                with open(extstr, "rt", encoding="utf-8") as infp:
                    tweet = json.load(infp)
        elif from_mem is not None:
            tweet = json.loads(from_mem)
        else:
            raise Exception("Cannot load from None")
        if tweet is None:
            raise Exception("Could not decode Tweet JSON")
        if tweet.get("truncated"):
            text = get_nested(tweet, "extended_tweet.full_text")
        else:
            text = get_nested(tweet, "text")
        if text is None:
            raise Exception("No text field found")
        quoted_status = None
        if include_quote:
            quoted_status = tweet.get("quoted_status")
            if quoted_status is not None:
                qtext = quoted_status.get("text", "")
                text += "\n" + qtext
        doc = Document(text)
        anns = doc.annset(outsetname)
        if tweet_ann:
            ann = anns.add(0, len(text), tweet_ann)
            features = ann.features
        else:
            features = doc.features
        if include_fields is None:
            include_fields = TWITTER_DEFAULT_INCLUDE_FIELDS
        for field in include_fields:
            if field.startswith("$"):
                if field == "$is_retweet_status":
                    rs = get_nested(tweet, "retweeted_status", silent=True)
                    if rs is not None:
                        features[field] = True
                continue
            val = get_nested(tweet, field, silent=True)
            if val is not None:
                features[field] = val
        if include_entities:
            if tweet.get("truncated"):
                entities = get_nested(tweet, "extended_tweet.entities", default={})
            else:
                entities = get_nested(tweet, "entities", default={})
        for etype, elist in entities.items():
            for ent in elist:
                start, end = ent["indices"]
                anns.add(start, end, etype)
        # TODO: if we have a quoted_status, add features and entities from there:
        # Essentially the same processing as for the original tweet, but at document offset
        # len(tweet)+1 (2?)
        return doc


class GateXmlLoader:
    """ """

    @staticmethod
    def value4objectwrapper(text):
        """This may one day convert things like lists, maps, shared objects to Python, but for
        now we always throw an exeption.

        Args:
          text: return:

        Returns:

        """
        raise Exception(
            "Cannot load GATE XML which contains gate.corpora.ObjectWrapper data"
        )

    @staticmethod
    def load(clazz, from_ext=None, ignore_unknown_types=False):
        """

        Args:
          clazz:
          from_ext: (Default value = None)
          ignore_unknown_types: (Default value = False)

        Returns:

        """
        # TODO: the code below is just an outline and needs work!
        # TODO: make use of the test document created in repo project-python-gatenlp
        import xml.etree.ElementTree as ET

        isurl, extstr = is_url(from_ext)
        if isurl:
            xmlstring = get_str_from_url(extstr, encoding="utf-8")
            root = ET.fromstring(xmlstring)
        else:
            tree = ET.parse(extstr)
            root = tree.getroot()

        # or: root = ET.fromstring(xmlstring)

        # check we do have a GATE document

        assert root.tag == "GateDocument"
        assert root.attrib == {"version": "3"}

        def parsefeatures(feats):
            """

            Args:
              feats:

            Returns:

            """
            features = {}
            for feat in list(feats):
                name = None
                value = None
                for el in list(feat):
                    if el.tag == "Name":
                        if el.get("className") == "java.lang.String":
                            name = el.text
                        else:
                            raise Exception(
                                "Odd Feature Name type: " + el.get("className")
                            )
                    elif el.tag == "Value":
                        cls_name = el.get("className")
                        if cls_name == "java.lang.String":
                            value = el.text
                        elif cls_name == "java.lang.Integer":
                            value = int(el.text)
                        elif cls_name == "java.lang.Long":
                            value = int(el.text)
                        elif cls_name == "java.math.BigDecimal":
                            value = float(el.text)
                        elif cls_name == "java.lang.Boolean":
                            value = bool(el.text)
                        # elif cls_name == "gate.corpora.ObjectWrapper":
                        #    value = GateXmlLoader.value4objectwrapper(el.text)
                        else:
                            if ignore_unknown_types:
                                print(
                                    f"Warning: ignoring feature with serialization type: {cls_name}",
                                    file=sys.stderr,
                                )
                            else:
                                raise Exception(
                                    "Unsupported serialization type: "
                                    + el.get("className")
                                )
                if name is not None and value is not None:
                    features[name] = value
            return features

        # get the document features
        docfeatures = {}
        feats = root.findall("./GateDocumentFeatures/Feature")

        docfeatures = parsefeatures(feats)

        textwithnodes = root.findall("./TextWithNodes")
        text = ""
        node2offset = {}
        curoff = 0
        for item in textwithnodes:
            if item.text:
                print("Got item text: ", item.text)
                text += item.text
                # TODO HTML unescape item text
                curoff += len(item.text)
            for node in item:
                nodeid = node.get("id")
                node2offset[nodeid] = curoff
                if node.tail:
                    # TODO: unescape item.text?
                    print("Gote node tail: ", node.tail)
                    text += node.tail
                    curoff += len(node.tail)

        annsets = root.findall("./AnnotationSet")

        annotation_sets = {}  # map name - set
        for annset in annsets:
            if annset.get("Name"):
                setname = annset.get("Name")
            else:
                setname = ""
            annots = annset.findall("./Annotation")
            annotations = []
            maxannid = 0
            for ann in annots:
                annid = int(ann.attrib["Id"])
                maxannid = max(maxannid, annid)
                anntype = ann.attrib["Type"]
                startnode = ann.attrib["StartNode"]
                endnode = ann.attrib["EndNode"]
                startoff = node2offset[startnode]
                endoff = node2offset[endnode]
                feats = ann.findall("./Feature")
                features = parsefeatures(feats)
                if len(features) == 0:
                    features = None
                annotation = {
                    "id": annid,
                    "type": anntype,
                    "start": startoff,
                    "end": endoff,
                    "features": features,
                }
                annotations.append(annotation)
            annset = {
                "name": setname,
                "annotations": annotations,
                "next_annid": maxannid + 1,
            }
            annotation_sets[setname] = annset

        docmap = {
            "text": text,
            "features": docfeatures,
            "offset_type": "p",
            "annotation_sets": annotation_sets,
        }

        doc = Document.from_dict(docmap)
        return doc


def determine_loader(
    clazz, from_ext=None, from_mem=None, offset_mapper=None, gzip=False, **kwargs
):
    """

    Args:
      clazz:
      from_ext: (Default value = None)
      from_mem: (Default value = None)
      offset_mapper: (Default value = None)
      gzip: (Default value = False)
      **kwargs:

    Returns:

    """
    first = None
    if from_mem:
        first = from_mem[0]
    else:
        with open(from_ext, "rt") as infp:
            first = infp.read(1)
    if first == "{":
        return JsonSerializer.load(
            clazz,
            from_ext=from_ext,
            from_mem=from_mem,
            offset_mapper=offset_mapper,
            gzip=gzip,
            **kwargs,
        )
    else:
        return MsgPackSerializer.load(
            clazz,
            from_ext=from_ext,
            from_mem=from_mem,
            offset_mapper=offset_mapper,
            gzip=gzip,
            **kwargs,
        )


DOCUMENT_SAVERS = {
    "text/plain": PlainTextSerializer.save,
    "text/plain+gzip": PlainTextSerializer.save_gzip,
    "text": PlainTextSerializer.save,
    "json": JsonSerializer.save,
    "jsongz": JsonSerializer.save_gzip,
    "bdocjs": JsonSerializer.save,
    "pickle": PickleSerializer.save,
    "bdocjsgz": JsonSerializer.save_gzip,
    "text/bdocjs": JsonSerializer.save,
    "text/bdocjs+gzip": JsonSerializer.save_gzip,
    "yaml": YamlSerializer.save,
    "bdocym": YamlSerializer.save,
    "yamlgz": YamlSerializer.save_gzip,
    "text/bdocym": YamlSerializer.save,
    "text/bdocym+gzip+": YamlSerializer.save_gzip,
    "msgpack": MsgPackSerializer.save,
    "bdocmp": MsgPackSerializer.save,
    "text/bdocmp": MsgPackSerializer.save,
    "application/msgpack": MsgPackSerializer.save,
    "html-ann-viewer": HtmlAnnViewerSerializer.save,
}
DOCUMENT_LOADERS = {
    "json": JsonSerializer.load,
    "jsongz": JsonSerializer.load_gzip,
    "bdocjs": JsonSerializer.load,
    "bdocjsgz": JsonSerializer.load_gzip,
    "text/bdocjs": JsonSerializer.load,
    "text/bdocjs+gzip": JsonSerializer.load_gzip,
    "yaml": YamlSerializer.load,
    "yamlgz": YamlSerializer.load_gzip,
    "bdocym": YamlSerializer.load,
    "bdocymzg: ": YamlSerializer.load_gzip,
    "text/bdocym": YamlSerializer.load,
    "text/bdocym+gzip": YamlSerializer.load_gzip,
    "msgpack": MsgPackSerializer.load,
    "bdocmp": MsgPackSerializer.load,
    "application/msgpack": MsgPackSerializer.load,
    "text/bdocmp": MsgPackSerializer.load,
    "jsonormsgpack": determine_loader,
    "text/plain": PlainTextSerializer.load,
    "text/plain+gzip": PlainTextSerializer.load_gzip,
    "text": PlainTextSerializer.load,
    "text/html": HtmlLoader.load,
    "html": HtmlLoader.load,
    "html-rendered": HtmlLoader.load_rendered,
    "gatexml": GateXmlLoader.load,
    "tweet": TweetLoader.load,
    "pickle": PickleSerializer.load,
}
CHANGELOG_SAVERS = {
    "json": JsonSerializer.save,
    "text/bdocjs+gzip": JsonSerializer.save_gzip,
    "text/bdocjs": JsonSerializer.save,
}
CHANGELOG_LOADERS = {
    "json": JsonSerializer.load,
    "text/bdocjs+gzip": JsonSerializer.load_gzip,
    "text/bdocjs": JsonSerializer.load,
}

# map extensions to document types
EXTENSIONS = {
    "bdocjs": "json",
    "bdocym": "yaml",
    "bdocym.gz": "text/bdocym+gzip",
    "bdoc.gz": "text/bdocjs+gzip",  # lets assume it is compressed json
    "bdoc": "jsonormsgpack",
    "bdocjs.gz": "text/bdocjs+gzip",
    "bdocjson": "json",
    "bdocmp": "msgpack",
    "txt": "text/plain",
    "txt.gz": "text/plain+gzip",
    "html": "text/html",
    "htm": "text/html",
    "pickle": "pickle",
}


def get_handler(filespec, fmt, handlers, saveload, what):
    """

    Args:
      filespec:
      fmt:
      handlers:
      saveload:
      what:

    Returns:

    """
    msg = f"Could not determine how to {saveload} {what} for format {fmt} in module gatenlp.serialization.default"
    if fmt:
        handler = handlers.get(fmt)
        if not handler:
            raise Exception(msg)
        return handler
    else:
        if not filespec:  # in case of save_mem
            raise Exception(msg)
        if isinstance(filespec, os.PathLike):
            wf = os.fspath(filespec)
        elif isinstance(filespec, str):
            wf = filespec
        else:
            raise Exception(msg)
        name, ext = os.path.splitext(wf)
        if ext == ".gz":
            ext2 = os.path.splitext(name)[1]
            if ext2:
                ext2 = ext2[1:]
            ext = ext2 + ext
        elif ext:
            ext = ext[1:]
        fmt = EXTENSIONS.get(ext)
        msg = f"Could not determine how to {saveload} {what} for format {fmt} and with " \
              "extension {ext} in module gatenlp.serialization.default"
        if not fmt:
            raise Exception(msg)
        handler = handlers.get(fmt)
        if not handler:
            raise Exception(msg)
        return handler


def get_document_saver(filespec, fmt):
    """

    Args:
      filespec:
      fmt:

    Returns:

    """
    return get_handler(filespec, fmt, DOCUMENT_SAVERS, "save", "document")


def get_document_loader(filespec, fmt):
    """

    Args:
      filespec:
      fmt:

    Returns:

    """
    return get_handler(filespec, fmt, DOCUMENT_LOADERS, "load", "document")


def get_changelog_saver(filespec, fmt):
    """

    Args:
      filespec:
      fmt:

    Returns:

    """
    return get_handler(filespec, fmt, CHANGELOG_SAVERS, "save", "changelog")


def get_changelog_loader(filespec, fmt):
    """

    Args:
      filespec:
      fmt:

    Returns:

    """
    return get_handler(filespec, fmt, CHANGELOG_LOADERS, "load", "changelog")
