"""
Module that implements the various ways of how to save and load documents and change logs.
"""
import sys
from decimal import Decimal
import xml.etree.ElementTree as ET
from gatenlp.document import Document
from gatenlp.utils import init_logger
from gatenlp.urlfileutils import is_url, get_str_from_url

logger = init_logger()


class GateXmlLoader:
    """
    Loader for JAVA GATE XML format. This supports document and annotation feature values for the following types:
    String, int, float, booleean, and the following containers containing recursively any of the supported types:
    Map, Array, List, Set (converted to list).
    """

    @staticmethod
    def context2txt(context):
        """Generate text from context info"""
        fname = context["fname"]
        node = context["node"]
        if node is None:
            nodetxt = ""
        else:
            nodetxt = ET.tostring(node, encoding='unicode', method="text")
        if context["ftype"] == "doc":
            return f"document feature {fname},\n    node={nodetxt}"
        else:
            atype = context["atype"]
            aset = context["aset"]
            offset = context["offset"]
            return f"annotation feature {fname} for ann type {atype} in set '{aset}' at offset {offset},\n    node={nodetxt}"

    @staticmethod
    def warning(txt, options, context):
        """Emit a warning or stay silent"""
        ctx = GateXmlLoader.context2txt(context)
        if options["show_warnings"]:
            logger.warning(f"{txt} for {ctx}")

    @staticmethod
    def error(txt, options, context):
        """Handle an error"""
        if options["ignore_errors"]:
            GateXmlLoader.warning(txt, options, context)
        else:
            ctx = GateXmlLoader.context2txt(context)
            raise Exception(f"{txt} for {ctx}")

    @staticmethod
    def xstream2python(node, options, context):
        """
        Convert a xstream node to a python object. The node should only have a single child.
        This is either a single Value.className=gate.corpora.ObjectWrapper node with a single value child, or
        a list of value nodes to initialize a container, or something not supported.
        """
        # if options["debug"]:
        #     print(f"DEBUG: Got element ({node.tag}):", ET.tostring(node))
        if node.tag == "gate.corpora.ObjectWrapper":
            children = list(node)
            if len(children) != 1:
                GateXmlLoader.error(
                    f"ObjectWrapper node with not exactly one child for {node} but: {len(children)}: {children}",
                    options, context)
                return None
            child = children[0]
            if child.tag != "value":
                GateXmlLoader.error(f"Child of Value tag is not value but {child.tag}", options, context)
                return None
            return GateXmlLoader.xstream2python(child, options, context)
        elif node.tag == "value":
            valueclass = node.attrib["class"]
            ret = None
            if valueclass == "set":
                GateXmlLoader.warning(f"Converting set to list", options, context)
                ret = []
                for el in node:
                    ret.append(GateXmlLoader.xstream2python(el, options, context))
            elif valueclass == "list" or valueclass.endswith("-array"):
                ret = []
                for el in node:
                    ret.append(GateXmlLoader.xstream2python(el, options, context))
            elif valueclass == "date":
                ret = node.text
            elif valueclass == "linked-hash-map" or valueclass == "hash-map" or valueclass == "map":
                ret = {}
                for el in node:
                    items = list(el)
                    if len(items) != 2:
                        GateXmlLoader.error(f"Not exactly two children for map content, but {len(items)}",
                                            options, context)
                        break
                    else:
                        key = GateXmlLoader.xstream2python(items[0], options, context)
                        value = GateXmlLoader.xstream2python(items[1], options, context)
                        ret[key] = value
            else:
                GateXmlLoader.error(f"Unsupported xstreaqm type: {valueclass}", options, context)
                ret = None
        else:
            # this is a node for nested values which are not ObjectWrapper, e.g. <string>
            ret = None
            if node.tag == "string":
                ret = node.text
                if ret is None:
                    ret = ""
            elif node.tag == "int":
                ret = int(node.text)
            elif node.tag == "long":
                ret = int(node.text)
            elif node.tag == "boolean":
                ret = (node.text == "true")
            elif node.tag == "set":
                GateXmlLoader.warning(f"Converting set to list", options, context)
                ret = []
                for el in node:
                    ret.append(GateXmlLoader.xstream2python(el, options, context))
            elif node.tag == "list" or node.tag.endswith("-array"):
                ret = []
                for el in node:
                    ret.append(GateXmlLoader.xstream2python(el, options, context))
            elif node.tag == "date":
                ret = node.text
            elif node.tag == "big-decimal":
                GateXmlLoader.warning(f"Converting BigDecimal to float", options, context)
                ret = float(Decimal(node.text))
            elif node.tag == "linked-hash-map" or node.tag == "hash-map" or node.tag == "map":
                ret = {}
                for el in node:
                    items = list(el)
                    if len(items) != 2:
                        GateXmlLoader.error(f"Not exactly two children for map content, but {len(items)}",
                                            options, context)
                        break
                    else:
                        key = GateXmlLoader.xstream2python(items[0], options, context)
                        value = GateXmlLoader.xstream2python(items[1], options, context)
                        ret[key] = value
            else:
                GateXmlLoader.error(f"Unknown type, nested tag: {node.tag}", options, context)
                ret = None
        return ret

    @staticmethod
    def value4objectwrapper(xmlstr, options, context):
        """
        Convert some xstream-converted Java values to Python values.

        Args:
            text: the xstream serialization of the value as encountered in the GATE XML
            options: options dictionary to influence error/warning behavior
            context: context information to add to warnings/error messages

        Returns:
            a python value. The value is None if the value could not get converted but the class is configured
            to ignore unknown types.

        Throws:
            Exception if a value cannot be converted to Python and the lcass is configured to not ignore unknown types.
        """
        tree = ET.fromstring(xmlstr)
        return GateXmlLoader.xstream2python(tree, options, context)

    @staticmethod
    def load(clazz,
             from_ext=None,
             ignore_errors=True,
             show_warnings=True,
             debug=False):
        """

        Args:
            clazz:
            from_ext: (Default value = None)
            ignore_errors: (default: False) if True, ignore errors and try to load what we can for the document,
                if False, throw and exception.
            show_warnings: (default: True) If an error occurs but ignore_errors is True, or if some conversion
                is carried out, show a warning.
            debug: if True, output detailed information about unsupported elements in the input to stderr

        Returns:
            Loaded document
        """
        options = dict(
            ignore_errors=ignore_errors,
            show_warnings=show_warnings,
            debug=debug
        )

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

        def parsefeatures(feats, ftype="Unknown", atype="Unknown", aset="Unknown", offset=None):
            """
            Parse the node for a feature map.

            Args:
              feats: iterable of Feature nodes

            Returns:
                The features
            """
            features = {}
            context = dict(
                ftype=ftype,
                atype=atype,
                aset=aset,
                offset=offset,
                fname=None,
                node=None
            )
            for feat in list(feats):
                name = None
                value = None
                for el in list(feat):
                    context["node"] = el
                    context["fname"] = name
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
                        elif cls_name == "gate.corpora.ObjectWrapper":
                            value = GateXmlLoader.value4objectwrapper(el.text, options, context)
                        else:
                            GateXmlLoader.error(f"Feature with unknown serialization type: {cls_name}",
                                                options, context)
                            value = None
                if name is not None and value is not None:
                    features[name] = value
            return features

        # get the document features
        docfeatures = {}
        feats = root.findall("./GateDocumentFeatures/Feature")

        docfeatures = parsefeatures(feats, ftype="doc")

        textwithnodes = root.findall("./TextWithNodes")
        text = ""
        node2offset = {}
        curoff = 0
        for item in textwithnodes:
            if item.text:
                text += item.text
                curoff += len(item.text)
            for node in item:
                nodeid = node.get("id")
                node2offset[nodeid] = curoff
                if node.tail:
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
                features = parsefeatures(feats, ftype="ann", atype=anntype, aset=setname, offset=startoff)
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


