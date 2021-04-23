"""
Module for the Pampac rule classe.
"""
from gatenlp.pam.pampac.pampac_parsers import PampacParser
from gatenlp.pam.pampac.actions import Actions


class Rule(PampacParser):
    """
    A matching rule: this defines the parser and some action (a function) to carry out if the rule matches
    as it is tried as one of many rules with a Pampac instance. Depending on select setting for pampac
    the action only fires under certain circumstances (e.g. the rule is the first that matches at a location).
    Rule is thus different from pattern.call() or Call(pattern, func) as these always call the function if
    there is a successful match.
    """

    def __init__(self, parser, *actions, priority=0):
        """
        Create a Rule.

        Args:
            parser: the parser to match for the rule
            action:  the action to perform, or a function to call. The action callable is passed the success object
                and the kwargs context and location
            priority: the priority of the rule
        """
        self.parser = parser
        self.action = Actions(*actions)
        self.priority = priority

    def set_priority(self, val):
        """
        Different way of setting the priority.
        """
        self.priority = val
        return self

    def parse(self, location, context):
        """
        Return the parse result. This does NOT automatically invoke the action if the parse result is a success.
        The invoking Pampac instance decides, based on its setting, for which matching rules the action is
        actually carried out.

        Returns:
            Success or failure of the parser

        """
        return self.parser.parse(location, context)
