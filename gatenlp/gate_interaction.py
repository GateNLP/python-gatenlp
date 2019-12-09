"""
Support for interacting between a GATE (java) process and a gatenlp (Python) process.
"""

import sys
import traceback
import gatenlp
from argparse import ArgumentParser
import inspect
import logging
from gatenlp.changelog import ChangeLog

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

instream = sys.stdin
ostream = sys.stdout
sys.stdout = sys.stderr


class _PrWrapper:
    def __init__(self):
        self.func_execute = None   # the function to process each doc
        self.func_execute_allowkws = False
        self.func_start   = None   # called when processing starts
        self.func_start_allowkws = False
        self.func_finish  = None   # called when processing finishes
        self.func_finish_allowkws = False
        self.func_result = None    # function for returning any over-corpus result
        self.func_result_allowkws = False
        self.func_reduce = None    # function for combining results
        self.func_reduce_allowkws = False
        self.script_parms = {}   # Script parms to pass to each execute

    def execute(self, doc):
        if self.func_execute_allowkws and self.script_parms:
            ret = self.func_execute(doc, **self.script_parms)
        else:
            ret = self.func_execute(doc)
        if ret is None:
            if doc.changelog is None:
                ret = doc
            else:
                ret = doc.changelog
        return ret

    def start(self, script_params):
        if script_params:
            self.script_parms = script_params
        # TODO: amend the script params with additional data from here?
        if self.func_start is not None:
            if self.func_start_allowkws and self.script_parms:
                self.func_start(**self.script_parms)
            else:
                self.func_start()

    def finish(self):
        if self.func_finish is not None:
            if self.func_finish_allowkws and self.script_parms:
                self.func_finish(**self.script_parms)
            else:
                self.func_finish()

    def result(self):
        if self.func_result is not None:
            if self.func_result_allowkws and self.script_parms:
                return self.func_result(**self.script_parms)
            else:
                return self.func_result()

    def reduce(self, resultslist):
        if self.func_reduce is not None:
            if self.func_reduce_allowkws and self.script_parms:
                ret = self.func_reduce(resultslist, **self.script_parms)
            else:
                ret = self.func_reduce(resultslist)
            return ret


def _check_exec(func):
    """
    Check the signature of the func to see if it is a proper
    execute function: must accept one (or more optional) args
    and can accept kwargs. This returns true of kwargs are accepted

    :param func: the function to check
    :return: true if the function accepts kwargs
    """
    argspec = inspect.getfullargspec(func)
    if len(argspec.args) == 1 \
          or len(argspec.args) == 2 and argspec.args[0] == "self" \
          or argspec.varargs is not None:
        pass
    else:
        raise Exception("Processing resource execution function does not accept exactly one or any number of arguments")
    if argspec.varkw is not None:
        return True
    else:
        return False


def _has_method(theobj, name):
    """
    Check if the object has a callable method with the given name,
    if yes return the method, otherwise return None

    :param theobj: the object that contains the method
    :param name: the name of the method
    :return: the method or None
    """
    tmp = getattr(theobj, name, None)
    if tmp is not None and callable(tmp):
        return tmp
    else:
        return None


def _pr_decorator(what):
    """
    This is the decorator to identify a class or function as a processing
    resource. This is made available with the name PR in the gatenlp
    package.

    This creates an instance of PRWrapper and registers all the relevant
    functions of the decorated class or the decorated function in the
    wrapper.

    :param what: the class or function to decorate.
    :return: modified class or function
    """
    gatenlp.gate_python_plugin_pr = "The PR from here!!!"

    wrapper = _PrWrapper()
    if inspect.isclass(what):
        what = what()   # create an instance
        # TODO: instead of this we could just as well store the instance and 
        # directly call the instance methods from the wrapper!
        execmethod = _has_method(what, "execute")
        if not execmethod:
            execmethod = _has_method(what, "__call__")
        if not execmethod:
            raise Exception("PR does not have an execute(doc) or __call__(doc) method.")
        allowkws = _check_exec(execmethod)
        wrapper.func_execute_allowkws = allowkws
        wrapper.func_execute = execmethod
        startmethod = _has_method(what, "start")
        if startmethod:
            wrapper.func_start = startmethod
            if inspect.getfullargspec(startmethod).varkw:
                wrapper.func_start_allowkws = True
        finishmethod = _has_method(what, "finish")
        if finishmethod:
            wrapper.func_finish = finishmethod
            if inspect.getfullargspec(finishmethod).varkw:
                wrapper.func_finish_allowkws = True
        resultmethod = _has_method(what, "result")
        if resultmethod:
            wrapper.func_result = resultmethod
            if inspect.getfullargspec(resultmethod).varkw:
                wrapper.func_result_allowkws = True
        reducemethod = _has_method(what, "reduce")
        if reducemethod:
            wrapper.func_reduce = reducemethod
            if inspect.getfullargspec(reducemethod).varkw:
                wrapper.func_reduce_allowkws = True

    elif inspect.isfunction(what):
        allowkws = _check_exec(what)
        wrapper.func_execute = what
        wrapper.func_execute_allowkws = allowkws
    else:
        raise Exception("Decorator applied to something that is not a function or class")
    gatenlp.gate_python_plugin_pr = wrapper
    return wrapper


class DefaultPr:
    def __call__(self, doc, **kwargs):
        logger.debug("DefaultPr: called __call__() with doc={}, kwargs={}".format(doc, kwargs))
        return doc

    def start(self, **kwargs):
        logger.debug("DefaultPr: called start() with kwargs={}".format(kwargs))
        logger.warning("Running DefaultPr: did you define a @GateNlpPr class or function?")
        return None

    def finish(self, **kwargs):
        logger.debug("DefaultPr: called finish() with kwargs={}".format(kwargs))
        logger.warning("Finished DefaultPr: did you define a @GateNlpPr class or function?")
        return None

    def result(self, **kwargs):
        logger.debug("DefaultPr: called result() with kwargs={}".format(kwargs))

    def reduce(self, resultlist, **kwargs):
        logger.debug("DefaultPr: called reduce() with results {} and kwargs={}".format(
            resultlist, kwargs))
        return None


def interact():
    """
    Starts and handles the interaction with a GATE python plugin process.
    This will get started by the GATE plugin if the interaction uses
    pipes, but can also be started separately for http/websockets.

    This MUST be called in the user's python file!
    The python file should also have one class or function decorated
    with the @gatenlp.PR  decorator to identify it as the
    processing resource to the system.

    :return:
    """
    logger.info("Using gatenlp version {}".format(gatenlp.__version__))
    # before we do anything we need to check if a PR has actually
    # been defined. If not, use our own default debugging PR
    if gatenlp.gate_python_plugin_pr is None:
        logger.warning("No processing resource defined with @GateNlpPr decorator, using default do-nothing")
        _pr_decorator(DefaultPr())

    pr = gatenlp.gate_python_plugin_pr

    argparser = ArgumentParser()
    argparser.add_argument("--mode", default="pipe",
                           help="Interaction mode: pipe|http|websockets")
    argparser.add_argument("--format", default="json",
                           help="Exchange format: json|flatbuffers")
    argparser.add_argument("-d", action="store_true",
                           help="Enable debugging: log to stderr")
    args = argparser.parse_args()

    if args.d:
        logger.setLevel(logging.DEBUG)
    if args.format == "json":
        from gatenlp.docformats.simplejson import loads, dumps
    elif args.format == "flatbuffers":
        raise Exception("Not implemented yet!")
    else:
        raise Exception("Not a supported interchange format: {}".format(args.format))

    logger.debug("Starting interaction args={}".format(args))
    if args.mode == "pipe":
        for line in instream:
            try:
                request = loads(line)
            except Exception as ex:
                logger.error("Unable to load from JSON:\n{}".format(line))
                raise ex
            logger.debug("Got request object: {}".format(request))
            cmd = request.get("command", None)
            stop_requested = False
            ret = None
            try:
                if cmd == "execute":
                    doc = request.get("data")
                    doc.set_changelog(ChangeLog())
                    pr.execute(doc)
                    # NOTE: for now we just discard what the method returns and always return
                    # the changelog instead!
                    ret = doc.changelog
                    logger.debug("Returning CHANGELOG: {}".format(ret))
                elif cmd == "start":
                    parms = request.get("data")
                    pr.start(parms)
                elif cmd == "finish":
                    pr.finish()
                elif cmd == "reduce":
                    results = request.get("results")
                    ret = pr.reduce(results)
                elif cmd == "result":
                    ret = pr.result()
                elif cmd == "stop":
                    stop_requested = True
                else:
                    raise Exception("Odd command received: {}".format(cmd))
                response = {
                    "data": ret,
                    "status": "ok",
                }
            except Exception as ex:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                error = repr(ex)
                info = "\n".join(traceback.format_tb(exc_traceback))
                response = {
                    "data": None,
                    "status": "error",
                    "error": error,
                    "info": info
                }
            logger.debug("Sending back response: {}".format(response))
            print(dumps(response), file=ostream)
            ostream.flush()
            if stop_requested:
                break
        # TODO: do any cleanup/restoring needed
        logger.debug("Finishing interaction")
    elif args.mode == "http":
        raise Exception("Mode http not implemented yet")
    elif args.mode == "websockets":
        raise Exception("Mode websockets not implemented yet")
    else:
        raise Exception("Not a valid mode: {}".format(args.mode))

