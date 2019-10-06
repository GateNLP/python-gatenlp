

# TODO: new implementation of processing resource:
# - maybe support running the old-fashioned pipe-based way 
# - support running as a single-process HTTP server accepting
#   a predefined set of commands for initialising, starting processing,
#   running on a document, stopping processing and shutting down
#   NOTE: this should support getting back a result datastructure (optionally)
#   when stopping processing (over-all-documents result!) even though GATE
#   does not support this (yet?)
# Future: maybe support websockets?

# We support two ways of how the python user can use this:
# - function decorator (for simple, pure function applications)
# - subclassing a class, override call, start, finish, abort 
# In both cases, the function call 
# - accepts a document, and arguments from the GATE PR, including 
#   one argument which is a map that comes from the script parms feature map
