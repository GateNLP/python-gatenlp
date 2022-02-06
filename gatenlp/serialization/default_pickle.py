"""
Module that implements the various ways of how to save and load documents and change logs.
"""
from gatenlp.urlfileutils import is_url, get_bytes_from_url
import pickle


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
