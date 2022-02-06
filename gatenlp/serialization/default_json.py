"""
Module that implements the various ways of how to save and load documents and change logs.
"""
import yaml
from collections import defaultdict
# import ruyaml as yaml
try:
    from yaml import CFullLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import FullLoader as Loader, Dumper
yaml_loader = yaml.Loader
yaml_dumper = yaml.Dumper
from gatenlp.urlfileutils import is_url, get_str_from_url, get_bytes_from_url
from gzip import open as gopen, compress, decompress
import warnings
import pickle


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

