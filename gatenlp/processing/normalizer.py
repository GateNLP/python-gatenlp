

# NOTE: a simple normalizer may only return a copy of the document with any annotations removed, so
# we do not have to adapt all the annotation offsets.
# Another aspect of normalizing may be that we just normalize "string" features within annotations,
# not the actual document text, that way, subsequent steps can act on the normalized
# feature values instead of the text.

class Normalizer:
    pass