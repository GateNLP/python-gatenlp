#!/usr/bin/env python
"""
Support for interacting between a GATE (java) process and a gatenlp (Python) process.
This is used by the Java GATE Python plugin.
"""

import sys
import os
import io
import traceback
from argparse import ArgumentParser
import inspect
import logging
from gatenlp.changelog import ChangeLog
from gatenlp.document import Document
from gatenlp.offsetmapper import OFFSET_TYPE_JAVA, OFFSET_TYPE_PYTHON
from gatenlp.utils import init_logger
from gatenlp.version import __version__ as gatenlp_version
import json

# NOTE: this is the global variable that holds the current function or class defined for interaction
# In order to avoid use of global, we use a list and just always use element 0
gate_python_plugin_pr = [None]


# We cannot simply do this, because on some systems Python may guess the wrong encoding for stdin:
# instream = sys.stdin
# Instead use utf-8 explicitly:
# NOTE: we only do this if we get the environment variable "FROMGATEPLUGIN" set, since this
# can interfere with normal use of gatenlp, with pytest etc!
if os.environ.get("FROMGATEPLUGIN"):
    instream = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    ostream = sys.stdout
    sys.stdout = sys.stderr

logger = init_logger("gate_interaction")


class _PrWrapper:
    def __init__(self):
        self.func_execute = None  # the function to process each doc
        self.func_execute_allowkws = False
        self.func_start = None  # called when processing starts
        self.func_start_allowkws = False
        self.func_finish = None  # called when processing finishes
        self.func_finish_allowkws = False
        self.func_reduce = None  # function for combining results
        self.func_reduce_allowkws = False
        self.script_parms = {}  # Script parms to pass to each execute
        self.logger = None

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
                return self.func_finish(**self.script_parms)
            else:
                return self.func_finish()

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

    Args:
      func: the function to check

    Returns:
      true if the function accepts kwargs

    """
    argspec = inspect.getfullargspec(func)
    if (
        len(argspec.args) == 1
        or len(argspec.args) == 2
        and argspec.args[0] == "self"
        or argspec.varargs is not None
    ):
        pass
    else:
        raise Exception(
            "Processing resource execution function does not accept exactly one or any number of arguments"
        )
    if argspec.varkw is not None:
        return True
    else:
        return False


def _has_method(theobj, name):
    """
    Check if the object has a callable method with the given name,
    if yes return the method, otherwise return None

    Args:
      theobj: the object that contains the method
      name: the name of the method

    Returns:
      the method or None

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

    Args:
      what: the class or function to decorate.

    Returns:
      modified class or function

    """
    wrapper = _PrWrapper()
    if inspect.isfunction(what):
        allowkws = _check_exec(what)
        wrapper.func_execute = what
        wrapper.func_execute_allowkws = allowkws
    elif inspect.isclass(what) or _has_method(what, "__call__"):
        # NOTE: functions also have a "__call__" attribute! This is why we need to check for function first.
        if inspect.isclass(what):
            what = (
                what()
            )  # if it is a class, create an instance, otherwise assume it is already an instance
        # TODO: instead of this we could just as well store the instance and
        # directly call the instance methods from the wrapper!
        execmethod = _has_method(what, "__call__")
        if not execmethod:
            raise Exception("PR does not have a __call__(doc) method.")
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
        reducemethod = _has_method(what, "reduce")
        if reducemethod:
            wrapper.func_reduce = reducemethod
            if inspect.getfullargspec(reducemethod).varkw:
                wrapper.func_reduce_allowkws = True
    else:
        raise Exception(
            f"Decorator applied to something that is not a function or class: {what}"
        )
    gate_python_plugin_pr[0] = wrapper
    return wrapper


class DefaultPr:
    def __call__(self, doc, **kwargs):
        logger.debug(
            "DefaultPr: called __call__() with doc={}, kwargs={}".format(doc, kwargs)
        )
        return doc

    def start(self, **kwargs):
        logger.debug("DefaultPr: called start() with kwargs={}".format(kwargs))
        logger.warning(
            "Running DefaultPr: did you define a @GateNlpPr class or function?"
        )
        return None

    def finish(self, **kwargs):
        logger.debug("DefaultPr: called finish() with kwargs={}".format(kwargs))
        logger.warning(
            "Finished DefaultPr: did you define a @GateNlpPr class or function?"
        )
        return None

    def reduce(self, resultlist, **kwargs):
        logger.debug(
            "DefaultPr: called reduce() with results {} and kwargs={}".format(
                resultlist, kwargs
            )
        )
        return None


def get_arguments(from_main=False):
    argparser = ArgumentParser()
    argparser.add_argument(
        "--mode",
        default="check",
        help="Interaction mode: pipe|http|websockets|file|dir|check (default: check)",
    )
    argparser.add_argument(
        "--format", default="json", help="Exchange format: json|json.gz|cjson"
    )
    argparser.add_argument("--path", help="File/directory path for modes file/dir")
    argparser.add_argument(
        "--out", help="Output file/directory path for modes file/dir"
    )
    argparser.add_argument(
        "-d", action="store_true", help="Enable debugging: log to stderr"
    )
    argparser.add_argument(
        "--log_lvl",
        type=str,
        help="Log level to use: DEBUG|INFO|WARNING|ERROR|CRITICAL",
    )
    argparser.add_argument(
        "--config_file",
        type=str,
        help="Config file path to pass on to the annotator (default: not set)",
    )
    argparser.add_argument(
        "--parms_file",
        type=str,
        help="The parms file to use for setting parameters",
    )
    if from_main:
        argparser.add_argument("pythonfile")
    args = argparser.parse_args()
    return args


def interact(args=None, annotator=None):
    """Starts and handles the interaction with a GATE python plugin process.
    This will get started by the GATE plugin if the interaction uses
    pipes, but can also be started separately for http/websockets.

    This MUST be called in the user's python file!
    The python file should also have one class or function decorated
    with the @gatenlp.PR  decorator to identify it as the
    processing resource to the system.

    :return:

    Args:
      args:  (Default value = None)

    Returns:

    """
    logger = init_logger(__name__)
    loglvls = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    # before we do anything we need to check if a PR has actually
    # been defined. If not, use our own default debugging PR
    if gate_python_plugin_pr[0] is None and annotator is None:
        logger.warning(
            "No processing resource defined with @GateNlpPr decorator or passed to interact, using default do-nothing"
        )
        _pr_decorator(DefaultPr)
    if annotator is not None:
        pr = _pr_decorator(annotator)
    else:
        pr = gate_python_plugin_pr[0]

    if args is None:
        args = get_arguments()
    if args.d:
        logger.setLevel(logging.DEBUG)
    if args.log_lvl:
        if args.log_lvl not in loglvls:
            raise Exception("Not a valid log level: {}".format(args.log_lvl))
        logger.setLevel(loglvls[args.log_lvl])

    if args.mode == "check":
        return

    logger.info("Using gatenlp version {}\n".format(gatenlp_version))

    logger.debug("Starting interaction args={}".format(args))
    if args.mode == "pipe":
        if args.format != "json":
            raise Exception("For interaction mode pipe, only format=json is supported")
        for line in instream:
            try:
                request = json.loads(line)
            except Exception as ex:
                logger.error("Unable to load from JSON:\n{}".format(line))
                raise ex
            logger.debug("Got request object: {}".format(request))
            cmd = request.get("command", None)
            stop_requested = False
            ret = None
            try:
                if cmd == "execute":
                    doc = Document.from_dict(request.get("data"))
                    om = doc.to_offset_type(OFFSET_TYPE_PYTHON)
                    doc.changelog = ChangeLog()
                    pr.execute(doc)
                    # NOTE: for now we just discard what the method returns and always return
                    # the changelog instead!
                    chlog = doc.changelog
                    # if we got an offset mapper earlier, we had to convert, so we convert back to JAVA
                    if om:
                        # replace True is faster, and we do not need the ChangeLog any more!
                        chlog.fixup_changes(
                            offset_mapper=om, offset_type=OFFSET_TYPE_JAVA, replace=True
                        )
                    ret = doc.changelog.to_dict()
                    logger.debug("Returning CHANGELOG: {}".format(ret))
                elif cmd == "start":
                    parms = request.get("data")
                    pr.start(parms)
                elif cmd == "finish":
                    ret = pr.finish()
                elif cmd == "reduce":
                    results = request.get("data")
                    ret = pr.reduce(results)
                elif cmd == "stop":
                    stop_requested = True
                else:
                    raise Exception("Odd command received: {}".format(cmd))
                response = {
                    "data": ret,
                    "status": "ok",
                }
            except Exception as ex:
                error = repr(ex)
                tb_str = traceback.format_exception(
                    etype=type(ex), value=ex, tb=ex.__traceback__
                )
                print("ERROR when running python code:", file=sys.stderr)
                for line in tb_str:
                    print(
                        line, file=sys.stderr, end=""
                    )  # what we get from traceback already has new lines
                info = "".join(tb_str)
                # in case we want the actual stacktrace data as well:
                st = [
                    (f.filename, f.lineno, f.name, f.line)
                    for f in traceback.extract_tb(ex.__traceback__)
                ]
                response = {
                    "data": None,
                    "status": "error",
                    "error": error,
                    "info": info,
                    "stacktrace": st,
                }
            logger.debug("Sending back response: {}".format(response))
            print(json.dumps(response), file=ostream)

            ostream.flush()
            if stop_requested:
                break
        # TODO: do any cleanup/restoring needed
        logger.debug("Finishing interaction")
    elif args.mode == "http":
        raise Exception("Mode http not implemented yet")
    elif args.mode == "websockets":
        raise Exception("Mode websockets not implemented yet")
    elif args.mode in ["file", "dir"]:
        if not args.path:
            raise Exception("Mode file or dir but no --path specified")
        fileext = ".bdoc" + args.format
        if args.mode == "file" and not os.path.isfile(args.path):
            raise Exception("Mode file but path is not a file: {}".format(args.path))
        elif args.mode == "dir" and not os.path.isdir(args.path):
            raise Exception(
                "Mode dir but path is not a directory: {}".format(args.path)
            )
        # we need to do this for mode file and dir: get the parms and run pr.start(parms):
        parms = {}
        # check if there is a parms file:
        if args.parms_file:
            with open(args.parms_file, "rt", encoding="utf-8") as infp:
                parms.update(json.load(infp))
        if args.config_file:
            parms["_config_file"] = args.config_file
        pr.start(parms)
        if args.mode == "file":
            logger.info(f"Loading file {args.path}")
            doc = Document.load(args.path)
            pr.execute(doc)
            pr.finish()
            if args.out:
                logger.info(f"Saving file to {args.out}")
                doc.save(args.out)
            else:
                logger.info(f"Saving file to {args.path}")
                doc.save(args.path)
        else:
            import glob
            files = glob.glob(args.path + os.path.sep + "*" + fileext)
            for file in files:
                logger.info("Loading file {}".format(file))
                doc = Document.load(file)
                pr.execute(doc)
                if args.out:
                    tofile = os.path.join(args.out, os.path.basename(file))
                    logger.info("Saving to {}".format(tofile))
                    doc.save(tofile)
                else:
                    logger.info("Saving to {}".format(file))
                    doc.save(file)
            pr.finish()
    else:
        raise Exception("Not a valid mode: {}".format(args.mode))


if __name__ == "__main__":
    # we run this from the command line so we need to also first load the PR code from the python file
    args = get_arguments(from_main=True)
    logger = init_logger(__name__)
    import importlib.util

    spec = importlib.util.spec_from_file_location("gateapp", args.pythonfile)
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)
    interact(args=args)
