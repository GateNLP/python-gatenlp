"""
Module that implements the various ways of how to save and load documents and change logs.
"""
import os
from random import choice
from string import ascii_uppercase
from gatenlp.document import Document
from gatenlp.gatenlpconfig import gatenlpconfig
import json as jsonlib

JS_JQUERY_URL = "https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"
JS_GATENLP_URL = "https://unpkg.com/gatenlp-ann-viewer@1.0.17/gatenlp-ann-viewer.js"
JS_JQUERY = f"<script src=\"{JS_JQUERY_URL}\"></script>"
JS_GATENLP = f"<script src=\"{JS_GATENLP_URL}\"></script>"
HTML_TEMPLATE_FILE_NAME = "gatenlp-ann-viewer.html"
JS_GATENLP_FILE_NAME = "gatenlp-ann-viewer-merged.js"

html_ann_viewer_serializer_js_loaded = False

SEP = "║"


def init_javscript():
    """
    Initialize the notebook/html javascript.
    """
    from IPython.display import display_html   # pylint: disable=C0415

    display_html(HtmlAnnViewerSerializer.javascript(), raw=True)


def show_colab(
        doc,
        htmlid=None,
        display=False,
        annspec=None,
        preselect=None,
        palette=None,
        cols4types=None,
        doc_style=None,
        row1_style=None,
        row2_style=None
):
    """
    Show htmldocumentviewe in a colab notebook.
    """
    from IPython.display import display_html, Javascript   # pylint: disable=C0415
    from IPython.display import display as i_display   # pylint: disable=C0415
    i_display(Javascript(url=JS_JQUERY_URL))
    i_display(Javascript(url=JS_GATENLP_URL))
    html = doc.save_mem(
        fmt="html-ann-viewer",
        notebook=True,
        add_js=False,
        offline=True,
        htmlid=htmlid,
        annspec=annspec,
        preselect=preselect,
        palette=palette,
        cols4types=cols4types,
        stretch_height=False,
        doc_style=doc_style,
        row1_style=row1_style,
        row2_style=row2_style,
    )
    if display:
        display_html(html, raw=True)
        return None
    else:
        return html


def show_notebook(
        doc,
        htmlid=None,
        display=False,
        annspec=None,
        preselect=None,
        palette=None,
        cols4types=None,
        doc_style=None,
        row1_style=None,
        row2_style=None
):
    """
    Show htmldocumentviewer in a jupyter notebook.
    """
    if not gatenlpconfig.notebook_js_initialized:
        init_javscript()
        gatenlpconfig.notebook_js_initialized = True
    html = doc.save_mem(
        fmt="html-ann-viewer",
        notebook=True,
        add_js=False,
        offline=True,
        htmlid=htmlid,
        annspec=annspec,
        preselect=preselect,
        palette=palette,
        cols4types=cols4types,
        stretch_height=False,
        doc_style=doc_style,
        row1_style=row1_style,
        row2_style=row2_style,
    )
    if display:
        from IPython.display import display_html  # pylint: disable=C0415
        display_html(html, raw=True)
        return None
    else:
        return html


class HtmlAnnViewerSerializer:
    """
    Serialization class for generating HTML/Javascript to view a document in an HTML page or in a Jupyter or
    Colab notebook.
    """

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
    def save(
            _clazz,
            inst,
            to_ext=None,
            to_mem=None,
            notebook=False,
            offline=False,
            add_js=True,
            htmlid=None,
            stretch_height=False,
            annspec=None,
            preselect=None,
            palette=None,
            cols4types=None,
            doc_style=None,
            row1_style=None,
            row2_style=None,
            **kwargs,
    ):
        """Convert a document to HTML for visualizing it.

        Args:
            _clazz: the class of the object to save
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
            stretch_height: if False, rows 1 and 2 of the viewer will not have the height set, but only
                min and max height (default min is 10em for row1 and 7em for row2, max is the double of those).
                If True, no max haight is set and instead the height is set to a percentage (default is
                67vh for row 1 and 30vh for row 2). The values used can be changed via gateconfig or the
                complete style for the rows can be set directly via row1_style and row2_style.
            annspec: if None, include all annotation sets and types, otherwise this should be a list of either
                set names, or tuples, where the first entry is a set name and the second entry is either a type
                name or list of type names to include.
            preselect: if not None, the set and type names to pre-select (show). This should have the same format
                as the annspec parameter.
            palette: if not None a list of colour codes (strings) usable in Javascript which will be used instead
                of the default palette.
            cols4types: if not None a dictionary mapping tuples (setname, typename) to a color. For the given
                setname and typename combinations, the colours from the palette (default or specified) will be
                overrriden.
            doc_style: if not None, any additional styling for the document text box, if None, use whatever
                is defined as gatenlpconfig.doc_html_repr_doc_style or do not use.
            row1_style: the style to use for the first row of the document viewer which shows the document text and
                annotation set and type panes. The default is gatenlpconfig.doc_html_repr_row1style_nostretch or
                gatenlpconfig.doc_html_repr_row1style_nostretch depending on the stretch_height parameter.
            row2_style: the style to use for the second row of the document viewer which shows the document or
                annotation features. The default is gatenlpconfig.doc_html_repr_row2style_nostretch or
                gatenlpconfig.doc_html_repr_row2style_nostretch depending on the stretch_height parameter.
            kwargs: swallow any other kwargs.

        Returns: if to_mem is True, returns the representation, otherwise None.

        """
        if not isinstance(inst, Document):
            raise Exception("Not a document!")
        parms = dict(presel_set=[], presel_list=[])
        doccopy = inst.deepcopy(annspec=annspec)
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
        if preselect is not None:
            # create a list of set/type lists and a set of set of setSEPtype for parms
            presel_set = set()
            presel_list = []
            for el in preselect:
                if isinstance(el, str):
                    for anntype in doccopy.annset(el).type_names:
                        settype = el + SEP + anntype
                        if settype not in presel_set:
                            presel_set.add(settype)
                            presel_list.append([el, anntype])
                elif isinstance(el, (list, tuple)) and len(el) > 1:
                    setname = el[0]
                    anntypes = el[1]
                    if isinstance(anntypes, str):
                        anntypes = [anntypes]
                    for anntype in anntypes:
                        settype = setname + SEP + anntype
                        if settype not in presel_set:
                            presel_set.add(settype)
                            presel_list.append([setname, anntype])
            parms["presel_set"] = list(presel_set)
            parms["presel_list"] = presel_list
        if notebook:
            str_start = "<!--STARTDIV-->"
            str_end = "<!--ENDDIV-->"
            idx1 = html.find(str_start) + len(str_start)
            idx2 = html.find(str_end)
            if htmlid:
                rndpref = str(htmlid)
            else:
                rndpref = "".join(choice(ascii_uppercase) for _i in range(10))
            html = html[idx1:idx2]
            html = f"""<div><style>#{rndpref}-wrapper {{ color: {txtcolor} !important; }}</style>
<div id="{rndpref}-wrapper">
{html}
</div></div>"""
            # replace the prefix with a random one
            html = html.replace("GATENLPID", rndpref)
        if palette is not None:
            parms["palette"] = palette
        if cols4types:
            newdict = {}
            for k, v in cols4types.items():
                if not isinstance(k, tuple) or not len(k) == 2 or not isinstance(v, str):
                    raise Exception("cols4types: must be a dictionary mapping (setname,typename) to color string")
                newdict[k[0]+SEP+k[1]] = v
            parms["cols4types"] = newdict
        else:
            parms["cols4types"] = {}
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
            if row1_style is None:
                row1_style = gatenlpconfig.doc_html_repr_row1style_stretch
            if row2_style is None:
                row2_style = gatenlpconfig.doc_html_repr_row2style_stretch
        else:
            if row1_style is None:
                row1_style = gatenlpconfig.doc_html_repr_row1style_nostretch
            if row2_style is None:
                row2_style = gatenlpconfig.doc_html_repr_row2style_nostretch
        html = html.replace("$$JAVASCRIPT$$", js, 1).replace("$$JSONDATA$$", json, 1)
        html = html.replace("$$JSONPARMS$$", jsonlib.dumps(parms), 1)
        html = html.replace("$$ROW1STYLE$$", row1_style, 1).replace(
            "$$ROW2STYLE$$", row2_style, 1
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
