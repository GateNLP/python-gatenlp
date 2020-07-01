
import json


class JsonSerializer:

    @staticmethod
    def save(clazz, doc, to_file=None, to_string=None, **kwargs):
        d = doc.to_dict()
        if to_string:
            return json.dumps(d)
        else:
            with open(to_file, "wt") as outfp:
                json.dump(d, outfp)

    @staticmethod
    def load(clazz, from_file=None, from_string=None, **kwargs):
        if from_string:
            d = json.loads(from_string)
            doc = clazz.from_dict(d)
        else:
            with open(from_file, "rt") as infp:
                d = json.load(infp)
                # print("DEBUG: dict=", d)
                doc = clazz.from_dict(d)
        return doc


FORMATS = dict(json=JsonSerializer)