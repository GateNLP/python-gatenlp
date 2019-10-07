"""
Support for interacting between a GATE (java) process and a gatenlp (Python) process.
Make this specifically work with gatelib-interaction!
TODO: check if we can somehow do this: save the original stdout and 
create our own handle, then for transmitting data, use that handle 
so that any stdout from library calls does not interfere with the 
data interchange??
It may be possible to this via
# at this point we should have nothing on the stdout buffer, i.e.
# initialisation should never write anything to stdout, so we should 
# do this before any more intensive initialisation!
old_stdout = sys.stdout  # this is where we want to send the data
# (actually this is always available as sys.__stdout__ )
sys.stdout = some outher destination we want everything else to go to, 
  maybe just sys.stderr? Or to io.StrinIO()?
# before terminating: close the new stdout and do whatever needed with it
# before terminating, flush and close the old stdout in a finally block
# to make sure
# the other side receives an end of file, also in the finally block, terminate


"""

# TODO
