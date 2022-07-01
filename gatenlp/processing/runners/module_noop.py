"""
No-operation pipeline for runner_dir2dir
"""
from gatenlp.processing.pipeline import Pipeline


def make_pipeline(args=None, nworkers=1, workernr=0):
    return Pipeline()


def result_processor(result=None):
    return None