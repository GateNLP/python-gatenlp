"""
Subpackage for modules related to pattern matching.
"""

# NOTES: Backreferences: too hard to implement this in a flexible way, simply use Filter on the final result
# TODO: check that Context.end is respected with all individual parsers: we should not match beyond that offset!
# TODO: figure out which parser parameters could be implemented as parser modifiers instead/in addition???
# TODO: implement Gazetteer(gaz, matchtype=None) parser? Or TokenGazetteer(gaz, ...)
# TODO: implement Forward() / fwd.set(fwd | Ann("X"))
# TODO: implement support for literal Text/Regexp: Seq(Ann("Token"), "text", regexp) and
#   Ann >> "text" and "text" >> Ann()
#   and Ann() | text etc.
# !!TODO: options for skip:
# !!TODO: * overlapping=True/False: sequence element can overlap with previous match
# !!TODO: * skip=True/False: skip forward in annotation list until we find annotation that fits
# !!TODO: * mingap=n, maxgap=n: gap between annotation must be in this range
# !!TODO: so A.followedby(B) is equal to Seq(A,B, mingap=0, maxgap=0, skip=False/True)
# mindist, maxdist: from start to start (mingap/maxgap; from end to start).
# !!TODO: implement memoize: save recursive result and check max recursion, modifier: parser.memoize(maxdepth=5)
#   for the wrapped parsers, before each call to the wrapped parser, we first check if the result is already in
#   the memotable and return it. If not, calculate recursion depth and Fail if too deep, otherwise call wrapped
#   parser and memoize (store Success or Failure)
