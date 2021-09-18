"""
Module for the PAMPAC pattern matcher.

Provides a language and classes for patterns, actions, rules.
"""

from gatenlp.pam.pampac.data import Location, Failure, Success, Result, Context
from gatenlp.pam.pampac.pampac_parsers import PampacParser, All, And, Ann, AnnAt, Call, Lookahead, Find
from gatenlp.pam.pampac.pampac_parsers import Function, N, Or, Seq, Text
from gatenlp.pam.pampac.pampac import Pampac, PampacAnnotator
from gatenlp.pam.pampac.rule import Rule
from gatenlp.pam.pampac.actions import AddAnn, Actions, UpdateAnnFeatures,RemoveAnn
from gatenlp.pam.pampac.actions import Getter
from gatenlp.pam.pampac.getters import GetAnn, GetEnd, GetType, GetText, GetStart
from gatenlp.pam.pampac.getters import GetFeature, GetFeatures, GetRegexGroup
