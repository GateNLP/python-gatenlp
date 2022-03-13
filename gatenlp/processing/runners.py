"""
Module that implements runners which can be used from the command line to run pipelines.
"""
import argparse
import importlib.util
import os
from typing import Callable
from gatenlp.corpora import DirFilesCorpus, DirFilesSource, DirFilesDestination

# Plan for multiprocessing: use a class which gets run in a ray actor and creates for each worker
# a separate copy of the pipeline, then run all those pipelines in parallel in each worker.
# the class is also responsible for creating their own source/dest or corpus instances to process
# just the documents allocated to the worker
# The make_pipeline code must properly handle nworkers and workernr

class SerialExecutor:
    def __init__(self, args=None):
        self.args = args

    def __call__(self):
        args = self.args
        if not os.path.exists(args.dir) or not os.path.isdir(args.dir):
            raise Exception(f"Does not exist or not a directory: {args.dir}")
        if args.outdir:
            if not os.path.exists(args.outdir) or not os.path.isdir(args.outdir):
                raise Exception(f"Output directory must exist: {args.outdir}")
            src = DirFilesSource(args.dir, ext=args.ext, fmt=args.fmt, recursive=args.recursive, sort=True)
            dest = DirFilesSource(args.outdir, ext=args.outext, fmt=args.outfmt, recursive=args.recursive, sort=True)
            corpus = None
        else:
            corpus = DirFilesCorpus(args.dir, ext=args.ext, fmt=args.fmt, recursive=args.recursive, sort=True)
            src = None
            dest = None

        if not os.path.exists(args.modulefile):
            raise Exception(f"Module file {args.modulefile} does not exist")
        spec = importlib.util.spec_from_file_location("gatenlp.tmprunner", args.modulefile)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        if not hasattr(mod, "make_pipeline"):
            raise Exception(f"Module {args.modulefile} does not define function make_pipeline(args=None)")
        if not isinstance(mod.make_pipeline, Callable):
            raise Exception(f"Module {args.modulefile} must contain a callable make_pipeline(args=None)")

        pipeline = mod.make_pipeline(args=args)
        if not isinstance(pipeline, Callable):
            raise Exception("make_pipeline must return a Callable")

        # for now just the simples possible way to do this
        n_in = 0
        n_error = 0
        n_out = 0
        if corpus is not None:
            for doc in corpus:
                try:
                    doc = pipeline(doc)
                    if doc is not None:
                        corpus.store(doc)
                        n_out += 1
                except Exception as ex:
                    print(f"Got an exception for document idx={n_in}/name={doc.name}: {str(ex)}")
                    n_error += 1
        else:
            for doc in src:
                try:
                    doc = pipeline(doc)
                    if doc is not None:
                        dest.append(doc)
                        n_out += 1
                except Exception as ex:
                    print(f"Got an exception for document idx={n_in}/name={doc.name}: {str(ex)}")
                    n_error += 1
        print(f"Documents read:     {n_in}")
        print(f"Processing errors:  {n_error}")
        print(f"Documents written:  {n_out}")


class RayExecutor:
    pass



def run_dir2dir():
    argparser = argparse.ArgumentParser(description="Run gatenlp pipeline on directory of documents")
    argparser.add_argument("dir", type=str,
                           help="Directory to process or input directory if --outdir is also specified"
                           )
    argparser.add_argument("--outdir", type=str,
                           help="If specified, read from dir, store result in outdir")
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
    args = argparser.parse_args()

    if args.nworkers == 1:
        exec = SerialExecutor(args=args)
        exec()
    else:
        exec = RayExecutor(args=args)
