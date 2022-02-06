"""
Module that implements the various ways of how to save and load documents and change logs.
"""
import sys
from gatenlp.document import Document
from gatenlp.urlfileutils import is_url, get_str_from_url


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
    def load(clazz, from_ext=None, ignore_unknown_types=False, warn_unknown_types=False):
        """

        Args:
            clazz:
            from_ext: (Default value = None)
            ignore_unknown_types: (default: False) if this is true, unknown types are ignored instead of raising
                an exception if one is encountered.
            warn_unknown_types: (default: False) If unknown types are ignored and this is true, a warning is logged
                for each occurrence of an unknown type.


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

        def parsefeatures(feats, ftype="Unknown", atype="Unknown", aset="Unknown", offset=None):
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
                                if warn_unknown_types:
                                    print(
                                        f"Warning: ignoring feature with serialization type: {cls_name}",
                                        file=sys.stderr,
                                    )
                            else:
                                tmptype = el.get("className")
                                hint = ": Use ignore_unknown_types=True option to ignore"
                                if ftype == "Unknown":
                                    raise Exception(f"Unsupported serialization type: {tmptype}"+hint)
                                elif ftype == "doc":
                                    raise Exception(
                                        f"Unsupported serialization type: {tmptype} for document feature {name}"+hint
                                    )
                                else:
                                    raise Exception(
                                        f"Unsupported serialization type: {tmptype} for annotation feature {name}"
                                        f"in {atype} annotation in set {aset} at offset {offset}" + hint
                                    )
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
                # TODO HTML unescape item text
                curoff += len(item.text)
            for node in item:
                nodeid = node.get("id")
                node2offset[nodeid] = curoff
                if node.tail:
                    # TODO: unescape item.text?
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


