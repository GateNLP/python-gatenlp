"""
Module that implements runners which can be used from the command line to run pipelines.
"""
import argparse
import importlib.util
import os
from typing import Callable
import signal
from collections import Iterable
import ray

from gatenlp.corpora import DirFilesCorpus, DirFilesSource, DirFilesDestination, NullDestination
from gatenlp.processing.pipeline import Pipeline
from gatenlp.utils import init_logger

# TODO: refactor get_pipeline_resultprocessor into separate functions to get the module, to
#    get the pipeline and to get the result processor from the module (passing the module)
#    Then add a function to also update the argparser if there is a "get_args()" method in the module.
# That way we can use arbitrary additional arguments to configure further processing
# This will come in handy for gatenlp-run where we also make the source/dest/corpus configurable
#
# TODO: refactor so that all processing that requires Ray is done in a different module which is only imported
#     when ray is actually used
#
# TODO: add native Python multiprocessing: use ray only if any of the ray-related options or "--ray"  is present

GLOBALS = dict(mod=None)

class LoggedException(Exception):
    pass

def load_module(args):
    if GLOBALS["mod"] is not None:
        return GLOBALS["mod"]
    if not os.path.exists(args.modulefile):
        raise Exception(f"Module file {args.modulefile} does not exist")
    spec = importlib.util.spec_from_file_location("gatenlp.tmprunner", args.modulefile)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    GLOBALS["mod"] = mod
    return mod


def get_add_args(args):
    mod = load_module(args)
    if hasattr(mod, "add_args"):
        return getattr(mod, "add_args")
    else:
        return None


def get_pipeline_resultprocessor(args, nworkers=1, workernr=0):
    """
    Get the instatiated pipeline and the process_result function from the module specified in
    the argparse args as option --modulefile.

    Args:
        args: argparse namespace
        nworkers: total number of workers
        workernr: the worker number (0-based)

    Returns:
        A list with the pipeline as the first and the process_result function as the second element.

    """
    mod = load_module(args)
    if not hasattr(mod, args.make_pipeline):
        raise Exception(f"Module {args.modulefile} does not define function {args.make_pipeline}(args=None, nworkers=1, workernr=0)")
    pipeline_maker = getattr(mod, args.make_pipeline)
    if not isinstance(pipeline_maker, Callable):
        raise Exception(f"Module {args.modulefile} must contain a callable {args.make_pipeline}(args=None, nworkers=1, workernr=0)")

    pipeline = pipeline_maker(args=args, workernr=workernr, nworkers=nworkers)
    if not isinstance(pipeline, Pipeline):
        raise Exception("make_pipeline must return a gatenlp.processing.pipeline.Pipeline")
    result_processor = None
    if args.process_result is not None:
        if not hasattr(mod, args.result_processor):
            raise Exception(f"Module does not define {args.process_result}")
        else:
            process_result = getattr(mod, args.process_result)
            if not isinstance(process_result, Callable):
                raise Exception(f"Result processor {args.process_result} is not Callable")
    return pipeline, result_processor


class Dir2DirExecutor:
    """
    Executor class.
    """
    def __init__(self, args=None, workernr=0, nworkers=1):
        """
        Initialize the executor.

        Args:
            args: argparse namespace
            workernr: 0-based index of the worker
            nworkers: total number of workers
        """
        self.args = args
        self.workernr = workernr
        self.nworkers = nworkers
        self.n_in = 0
        self.n_out = 0
        self.n_none = 0
        self.logger = None
        self.logger = init_logger(name="Dir2DirExecutor")
        self.result_processor = None
        self.error = False

    def get_inout(self):
        """
        Return a list with either the corpus or the source and destination to use for processing
        """
        args = self.args
        if not os.path.exists(args.dir) or not os.path.isdir(args.dir):
            raise Exception(f"Does not exist or not a directory: {args.dir}")
        if args.outdir or args.outnone:
            if args.outnone:
                dest =NullDestination()
            else:
                if not os.path.exists(args.outdir) or not os.path.isdir(args.outdir):
                    raise Exception(f"Output directory must exist: {args.outdir}")
                dest = DirFilesDestination(
                    args.outdir, "relpath", fmt=args.fmt, ext=args.ext
                )
            src = DirFilesSource(
                args.dir, exts=args.ext, fmt=args.fmt, recursive=args.recursive, sort=True,
                nparts=args.nworkers, partnr=self.workernr
            )
            return [src, dest]
        else:
            corpus = DirFilesCorpus(
                args.dir, ext=args.ext, fmt=args.fmt, recursive=args.recursive, sort=True,
                nparts=args.nworkers, partnr=self.workernr
            )
            return [corpus]

    def run_pipe(self, pipeline, inout):
        """
        Run the given pipeline on the given input/output configuration.

        Args:
            pipeline: processing pipeline
            inout: list with input/output configuration

        Returns:

        """
        flags = dict(interrupted = False)
        logpref = f"Worker {self.workernr+1} of {self.nworkers}: "

        def siginthandler(sig, frame):
            self.error = True
            flags["interrupted"] = True
            self.logger.warning(f"{logpref}received SIGINT signal")

        signal.signal(signal.SIGINT, siginthandler)

        if len(inout) == 2:   # src -> dest
            for ret in pipeline.pipe(inout[0]):
                if flags["interrupted"]:
                    self.logger.warning(f"{logpref}interrupted by SIGINT")
                    break
                if ret is not None:
                    if isinstance(ret, Iterable):
                        for doc in ret:
                            inout[1].append(doc)
                    else:
                        inout[1].append(ret)
                else:
                    self.n_none += 1
                self.n_in = inout[0].n
                self.n_out = inout[1].n
                if self.n_out % self.args.log_every == 0:
                    self.logger.info(f"{logpref}{self.n_in} read, {self.n_none} were None, {self.n_out} returned")
            self.n_in = inout[0].n
            self.n_out = inout[1].n
        else:
            self.n_in = 0
            for ret in pipeline.pipe(inout[0]):
                if flags["interrupted"]:
                    self.logger.warning(f"{logpref}interrupted by SIGINT")
                    break
                if ret is not None:
                    if isinstance(ret, list):
                        if len(ret) > 1:
                            raise Exception(f"{logpref}Pipeline {pipeline} returned {len(ret)} documents for corpus index {self.n_in}")
                        for doc in ret:
                            inout[0].store(doc)
                            self.n_out += 1
                    else:
                        inout[0].store(ret)
                        self.n_out += 1
                else:
                    self.n_none += 1
                self.n_in += 1
                if self.n_out % self.args.log_every == 0:
                    self.logger.info(f"{logpref}{self.n_in} read, {self.n_none} were None, {self.n_out} returned")

    def run(self):
        """
        Run processing with the pipeline.

        Returns:
            The result returned by the pipeline finish() method
        """
        logpref = f"Worker {self.workernr+1} of {self.nworkers}: "
        pipeline, self.result_processor = get_pipeline_resultprocessor(self.args)
        self.logger.info(f"{logpref}got pipeline {pipeline}")
        inout = self.get_inout()
        self.logger.info(f"{logpref}got In/Out {inout}")
        have_error = False
        try:
            pipeline.start()
        except Exception as ex:
            self.logger.error(f"Pipeline start aborted", exc_info=ex)
            self.error = True
            raise LoggedException()
        self.logger.info(f"{logpref}pipeline start() completed")
        self.logger.info(f"{logpref}running pipeline")
        try:
            self.run_pipe(pipeline, inout)
            self.logger.info(
                f"{logpref}pipeline running completed: {self.n_in} read, {self.n_none} were None, {self.n_out} returned")
        except Exception as ex:
            self.logger.error(f"Pipeline running aborted, {self.n_in} read, {self.n_none} were None, {self.n_out} returned",
                              exc_info=ex)
            # we continue to calculate any incomplete result, but remember that we had an error
            self.error = True
        try:
            ret = pipeline.finish()
            self.logger.info(f"{logpref}pipeline finish() completed")
            # only return the result value if we have a result processor defined!
            if self.args.process_result:
                return ret
            else:
                return
        except Exception as ex:
            self.logger.error(f"Pipeline finish aborted", exc_info=ex)
            self.error = True
            raise LoggedException()


@ray.remote
def ray_executor(args=None, workernr=0, nworkers=1):
    executor = Dir2DirExecutor(args, workernr=workernr, nworkers=nworkers)
    ret = executor.run()
    return dict(result=ret, error=executor.error, n_in=executor.n_in, n_out=executor.n_out, n_none=executor.n_none)


def build_argparser():
    argparser = argparse.ArgumentParser(
        description="Run gatenlp pipeline on directory of documents",
        epilog="The module should define make_pipeline(args=None, workernr=0) and result_processor(result=None)" +
               " and can optionally define add_args(argparser) to inject additional arguments into the argparser"
    )
    argparser.add_argument("dir", type=str,
                           help="Directory to process or input directory if --outdir is also specified"
                           )
    argparser.add_argument("--outdir", type=str,
                           help="If specified, read from dir, store result in outdir")
    argparser.add_argument("--outnone", action="store_true",
                           help="If specified, --outdir is ignored, if present and the output of the pipeline is ignored")
    argparser.add_argument("--fmt", choices=["bdocjs"],
                           help="Format of documents in dir (none: determine from file extension)")
    argparser.add_argument("--outfmt", choices=["bdocjs"],
                           help="Format of documents in outdir (only used if --outdir is specified)")
    argparser.add_argument("--ext", choices=["bdocjs"], default="bdocjs",
                           help="File extension of documents in dir (bdocjs)")
    argparser.add_argument("--outext", choices=["bdocjs"],
                           help="File extension of documents in outdir (only used if --outdir is specified)")
    argparser.add_argument("--recursive", action="store_true",
                           help="If specified, process all documents in all subdirectories as well")
    argparser.add_argument("--modulefile", required=True,
                           help="Module file that contains the make_pipeline(args=None, workernr=0) definition")
    argparser.add_argument("--nworkers", default=1, type=int,
                           help="Number of workers to run (1)")
    argparser.add_argument("--ray_address", type=str, default=None,
                           help="If specified, connect to ray cluster with that redis address, otherwise start own local cluster")
    argparser.add_argument("--log_every", default=1000, type=int,
                           help="Log progress message every n read documents (1000)")
    argparser.add_argument("--make_pipeline", type=str, default="make_pipeline",
                           help="Name of the pipeline factory function (make_pipeline)")
    argparser.add_argument("--process_result", type=str, default=None,
                           help="Name of result processing function, if None, results are ignored (None)")
    argparser.add_argument("--debug", action="store_true",
                           help="Show DEBUG logging messages")
    return argparser


def run_dir2dir():
    argparser = build_argparser()
    args, extra = argparser.parse_known_args()
    # if we detect extra args, try to find the add_args function in the module:
    add_args_fn = get_add_args(args)
    if add_args_fn is not None:
        argparser = build_argparser()
        add_args_fn(argparser)
        args = argparser.parse_args()
    elif len(extra) > 0:
        raise Exception(f"Unknown args, but no add_args function in module: {extra}")

    logger = init_logger(name="run_dir2dir", debug=args.debug)
    if args.nworkers == 1:
        logger.info("Running SerialExecutor")
        exec = Dir2DirExecutor(args=args)
        try:
            result = exec.run()
            if args.process_result:
                logger.info("Processing result")
                exec.result_processor(result=result)
            if exec.error:
                logger.error(f"Processing ended with ERROR!!!")
            else:
                logger.info(f"Processing ended normally")
        except LoggedException:
            logger.error(f"Processing ended with ERROR!!!")
        except Exception as ex:
            logger.error(f"Processing ended with ERROR!!!", exc_info=ex)
    else:
        logger.info("Running RayExecutor")
        assert args.nworkers > 1
        if args.ray_address is None:
            logger.info(f"Starting Ray, using {args.nworkers} workers")
            rayinfo = ray.init()
        else:
            rayinfo = ray.init(address=args.ray_address)
            logger.info(f"Connected to Ray cluster at {args.ray_address} using {args.nworkers}")
        logger.info(f"Ray available: {rayinfo}")
        workers = []
        for k in range(args.nworkers):
            worker = ray_executor.remote(args, workernr=k, nworkers=args.nworkers)
            workers.append(worker)
            logger.info(f"Started worker {k}: {worker}")
        remaining = workers

        def siginthandler(sig, frame):
            for worker in workers:
                logger.warning(f"KILLING worker {worker}")
                ray.cancel(worker)

        signal.signal(signal.SIGINT, siginthandler)
        while True:
            finished, remaining = ray.wait(remaining, num_returns=1, timeout=10.0)
            if len(finished) > 0:
                logger.info(f"Finished: {finished} ({len(finished)} so far, {len(remaining)} remaining)")
            if len(remaining) == 0:
                logger.info("All workers finished, processing results")
                break
        results_list = ray.get(workers)
        pipeline_results = [r["result"] for r in results_list]
        have_error = False
        total_in = 0
        total_none = 0
        total_out = 0
        for worker, ret in zip(workers, results_list):
            if ret["error"]:
                logger.error(f"Worker {worker} ABORTED, {ret['n_in']} read, {ret['n_none']} were None, {ret['n_out']} returned")
                have_error = True
            else:
                logger.info(f"Worker {worker} finished, {ret['n_in']} read, {ret['n_none']} were None, {ret['n_out']} returned")
            total_in += ret["n_in"]
            total_none += ret["n_none"]
            total_out += ret["n_out"]
        logger.info(f"Total processed:  {total_in} read, {total_none} were None, {total_out} returned")
        if args.process_result:
            logger.info(f"Processing any results")
            logger.info(f"Creating pipeline for workernr -1")
            pipeline, resultprocessor = get_pipeline_resultprocessor(args, workernr=-1, nworkers=1)
            logger.info(f"Combining results")
            result = pipeline.reduce(results_list)
            logger.info("Processing results")
            try:
                resultprocessor(result=result)
            except Exception as ex:
                logger.error(f"Result processor error", exc_info=ex)
                have_error = True
        logger.info("Shutting down Ray ...")
        ray.shutdown()
        if have_error:
            logger.error(f"Processing ended with ERROR!!!")
        else:
            logger.info("Processing ended normally")
