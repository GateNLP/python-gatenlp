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

# Conventions used:
# specify a module to load by each process
# optionally specify a function to call which will return  the pipeline to run. Function
#    should take args and workernr as argument. If not specified defaults to make_pipeline(args, workernr)
# This module always runs worker number 0
# other actors get started and passed the args (which contain nworkers) and workern
# a finished actor returns its pipeline results, if any, which must be pickleable
# this module runs the reduce method on all results
#
# error handling:
# a pipeline may ignore errors, but if it raises an exception the actor terminates and returns an error
#    HOW TO DO THAT?
# if worker 0 terminates or any actor terminates, all other actors get terminated
# if worker 0 receives an term signal everything gets terminated


# Plan for multiprocessing: use a class which gets run in a ray actor and creates for each worker
# a separate copy of the pipeline, then run all those pipelines in parallel in each worker.
# the class is also responsible for creating their own source/dest or corpus instances to process
# just the documents allocated to the worker
# The make_pipeline code must properly handle nworkers and workernr


# NOTE: make_pipeline must return a Pipeline which must have pipe() (which could be implemented as
# iterating over __call__()). The Pipeline also must have start() finish() and reduce()

# !!! BY CONVENTION: if the module which defines make_pipeline also implements process_result(results=results, args=args)

def do_nothing(*args, **kwargs):
    pass


def get_pipeline_resultprocessor(args, nworkers=1, workernr=0):
    if not os.path.exists(args.modulefile):
        raise Exception(f"Module file {args.modulefile} does not exist")
    spec = importlib.util.spec_from_file_location("gatenlp.tmprunner", args.modulefile)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    if not hasattr(mod, "make_pipeline"):
        raise Exception(f"Module {args.modulefile} does not define function make_pipeline(args=None)")
    if not isinstance(mod.make_pipeline, Callable):
        raise Exception(f"Module {args.modulefile} must contain a callable make_pipeline(args=None)")

    pipeline = mod.make_pipeline(args=args, workernr=workernr, nworkers=nworkers)
    if not isinstance(pipeline, Pipeline):
        raise Exception("make_pipeline must return a gatenlp.processing.pipeline.Pipeline")
    if not hasattr(mod, "process_result"):
        result_processor = do_nothing
    else:
        result_processor = mod.process_result
    return pipeline, result_processor


class BaseExecutor:
    def __init__(self, args=None, workernr=0, nworkers=1):
        self.args = args
        self.workernr = workernr
        self.nworkers = nworkers
        self.n_in = 0
        self.n_out = 0
        self.n_none = 0
        self.logger = None

    def get_inout(self):
        """
        Return either the corpus or a tuple (src, dest) to use for processing
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
                dest = DirFilesSource(
                    args.outdir, exts=args.outext, fmt=args.outfmt, recursive=args.recursive, sort=True,
                    paths_from="relpath"
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
        if len(inout) == 2:   # src -> dest
            for ret in pipeline.pipe(inout[0]):
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
                if self.n_in % self.args.log_every == 0:
                    self.logger.info(f"Worker {self.workernr+1} of {self.nworkers}: {self.n_in} read, {self.n_none} were None, {self.n_out} returned")
        else:
            self.n_in = 0
            for ret in pipeline.pipe(inout[0]):
                if ret is not None:
                    if isinstance(ret, list):
                        if len(ret) > 1:
                            raise Exception(f"Pipeline {pipeline} returned {len(ret)} documents for corpus index {self.n_in}")
                        for doc in ret:
                            inout[0].store(doc)
                            self.n_out += 1
                    else:
                        inout[0].store(ret)
                        self.n_out += 1
                else:
                    self.n_none += 1
                self.n_in += 1
                if self.n_in % self.args.log_every == 0:
                    self.logger.info(f"Worker {self.workernr+1} of {self.nworkers}: {self.n_in} read, {self.n_none} were None, {self.n_out} returned")


class SerialExecutor(BaseExecutor):

    def __init__(self, args=None):
        super().__init__(args, workernr=0, nworkers=1)
        self.logger = init_logger(name="SerialExecutor")

    def run(self):
        interrupted = False

        def siginthandler(sig, frame):
            global interrupted
            self.logger.error("Got interrupted by signal SIGINT")
            interrupted = True

        signal.signal(signal.SIGINT, siginthandler)
        self.logger.info("Signal handler installed")

        pipeline, _ = get_pipeline_resultprocessor(self.args)
        self.logger.info(f"Got pipeline: {pipeline}")
        inout = self.get_inout()
        self.logger.info(f"Got In/Out: {inout}")
        pipeline.start()
        self.logger.info("pipeline start() completed")
        self.logger.info("Running pipeline")
        self.run_pipe(pipeline, inout)
        ret = pipeline.finish()
        self.logger.info(f"Pipeline running completed: {self.n_in} read, {self.n_none} were None, {self.n_out} returned")
        self.logger.info("pipeline finish() completed")
        return ret

class RayExecutor(BaseExecutor):
    def __init__(self, args=None, workernr=0, nworkers=1):
        super().__init__(args, workernr=workernr, nworkers=nworkers)
        self.logger = init_logger(name="RayExecutor")

    def run(self):
        self.logger.info(f"Ray worker {self.workernr+1}: starting")
        pipeline, _ = get_pipeline_resultprocessor(self.args, nworkers=self.nworkers, workernr=self.workernr)
        inout = self.get_inout()
        pipeline.start()
        self.run_pipe(pipeline, inout)
        ret = pipeline.finish()
        self.logger.info(f"Ray worker {self.workernr+1}: finished")
        return ret


@ray.remote
def ray_executor(args=None, workernr=0, nworkers=1):
    executor = RayExecutor(args, workernr=workernr, nworkers=nworkers)
    ret = executor.run()
    return ret

def run_dir2dir():
    argparser = argparse.ArgumentParser(
        description="Run gatenlp pipeline on directory of documents",
        epilog="The module should define make_pipeline(args=None, workernr=0) and result_processor(result=None)"
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
    argparser.add_argument("--redis", type=str, default=None,
                           help="If specified, connect to ray cluster with that redis address, otherwise start own local cluster")
    argparser.add_argument("--log_every", default=1000, type=int,
                           help="Log progress message every n read documents (1000)")
    argparser.add_argument("--debug", action="store_true",
                           help="Show DEBUG logging messages")
    args = argparser.parse_args()

    logger = init_logger(name="run_dir2dir", debug=args.debug)
    if args.nworkers == 1:
        logger.info("Running SerialExecutor")
        exec = SerialExecutor(args=args)
        exec.run()
    else:
        logger.info("Running RayExecutor")
        assert args.nworkers > 1
        if args.redis is None:
            logger.info(f"Starting Ray, using {args.nworkers} actors")
            rayinfo = ray.init()
        else:
            rayinfo = ray.init(redis_address=args.redis)
            logger.info(f"Connected to Ray cluster at {args.redis} using {args.nworkers}")
        logger.info(f"Ray available: {rayinfo}")
        actors = []
        handles = []
        for k in range(args.nworkers):
            actor = ray_executor.remote(args, workernr=k, nworkers=args.nworkers)
            actors.append(actor)
            logger.info(f"Started actor {k}: {actor}")
        remaining = actors
        while True:
            finished, remaining = ray.wait(remaining, num_returns=1, timeout=10.0)
            if len(finished) > 0:
                logger.info(f"Finished: {finished} ({len(finished)} so far, {len(remaining)} remaining)")
            if len(remaining) == 0:
                logger.info("All actors finished, processing results")
                break
        pipeline, resultprocessor = get_pipeline_resultprocessor(args, workernr=-1, nworkers=1)
        results_list = ray.get(actors)
        result = pipeline.reduce(results_list)
        resultprocessor(result=result)
