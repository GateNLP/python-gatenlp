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
