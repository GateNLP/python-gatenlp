"""
Module that implements the various ways of how to save and load documents and change logs.
"""
from collections import defaultdict
from gatenlp.document import Document
from gatenlp.utils import get_nested
from gatenlp.urlfileutils import is_url, get_str_from_url, get_bytes_from_url
import warnings


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


class TweetV1Serializer:

    @staticmethod
    def doc2twitterv1dict(doc, annsets=None, prefix_sep=None):
        d = doc.to_dict(annsets=annsets)
        ret = {"full_text": doc.text}
        ents = defaultdict(list)
        for setname, annset in d.get("annotation_sets", {}).items():
            for ann in annset.get("annotations", []):
                anntype = ann["type"]
                if prefix_sep is not None and setname != "":
                    anntype = setname + prefix_sep + anntype
                annlist = ents[anntype]
                twitterann = {
                    "indices": [ann["start"], ann["end"]]
                }
                twitterann.update(ann["features"])
                annlist.append(twitterann)
        ret["entities"] = ents
        return ret

    @staticmethod
    def save(
        clazz,
        inst,
        to_ext=None,
        to_mem=None,
        annsets=None,
        prefix_sep=None,
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
            annsets: which annotation sets and types to include, list of set names or (setanmes, types) tuples
            prefix_types: if not None, prefix all types with the name of the annotation set the annotation comes from
                and use the given string as the separator (can be the empty string for no seaparator).
                For annotations from the default set the type stays unchanged.
          **kwargs:
        """
        d = TweetV1Serializer.doc2twitterv1dict(inst, annsets=annsets, prefix_sep=prefix_sep)
        if to_mem:
            return json.dumps(d)
        else:
            with open(to_ext, JSON_WRITE) as outfp:
                json.dump(d, outfp)

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

