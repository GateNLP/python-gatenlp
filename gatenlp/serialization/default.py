
import json


class JsonSerializer:

    @staticmethod
    def save(clazz, inst, to_file=None, to_string=None, offset_type=None, offset_mapper=None, **kwargs):
        d = inst.to_dict(offset_type=offset_type, offset_mapper=offset_mapper, **kwargs)
        if to_string:
            return json.dumps(d)
        else:
            with open(to_file, "wt") as outfp:
                json.dump(d, outfp)

    @staticmethod
    def load(clazz, from_file=None, from_string=None, offset_mapper=None, **kwargs):
        if from_string:
            d = json.loads(from_string)
            doc = clazz.from_dict(d, offset_mapper=offset_mapper, **kwargs)
        else:
            with open(from_file, "rt") as infp:
                d = json.load(infp)
                # print("DEBUG: dict=", d)
                doc = clazz.from_dict(d, offset_mapper=offset_mapper, **kwargs)
        return doc


FORMATS = dict(json=JsonSerializer)