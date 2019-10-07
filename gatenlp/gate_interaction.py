"""
Support for interacting between a GATE (java) process and a gatenlp (Python) process.
Make this specifically work with gatelib-interaction!
TODO: check if we can somehow do this: save the original stdout and 
create our own handle, then for transmitting data, use that handle 
so that any stdout from library calls does not interfere with the 
data interchange??
"""

# TODO
