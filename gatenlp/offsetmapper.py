"""
Module that implements the OffsetMapper class for mapping between Java-style and Python-style string offsets.
Java strings are represented as UTF16 while Python strings are represented as Unicode code points, so offsets
differ if a Unicode character needs more than one UTF16 code unit.
"""

import numbers

OFFSET_TYPE_JAVA = "j"
OFFSET_TYPE_PYTHON = "p"


class OffsetMapper:
    def __init__(self, text: str):
        """
        Calculate the tables for mapping unicode code points to utf16 code units.

        NOTE: currently this optimizes for conversion speed at the cost of memory, with one special case:
        if after creating the java2python table we find that all offsets are identical, we discard
        the tables and just set a flag for that.

        Args:
            text: the text as a python string
        """
        # for now, remove dependency on numpy and use simple python lists of integers
        # import numpy as np
        cur_java_off = 0
        python2java_list = [0]
        java2python_list = []
        last = len(text) - 1
        for i, c in enumerate(text):
            # get the java size of the current character
            width = int(len(c.encode("utf-16be")) / 2)
            assert width == 1 or width == 2
            # the next java offset we get by incrementing the java offset by the with of the current char
            cur_java_off += width
            if i != last:
                python2java_list.append(cur_java_off)
            # i is the current python offset, so we append as many times to java2python_list as we have width
            java2python_list.append(i)
            if width == 2:
                java2python_list.append(i)
        if len(java2python_list) == len(text):
            self.python2java = None
            self.java2python = None
            self.bijective = len(text)
        else:
            python2java_list.append(python2java_list[-1] + 1)
            # self.python2java = np.array(python2java_list, np.int32)
            self.python2java = python2java_list
            # self.java2python = np.array(java2python_list, np.int32)
            java2python_list.append(java2python_list[-1] + 1)
            self.java2python = java2python_list
            self.bijective = None  # if we have identical offsets, this is set to the length of the text instead

    def _convert_from(self, offsets, from_table=None):
        """

        Args:
          offsets:
          from_table:  (Default value = None)

        Returns:

        """
        if from_table is None:
            return offsets
        if isinstance(offsets, numbers.Integral):
            return int(from_table[offsets])
        ret = []
        for offset in offsets:
            ret.append(int(from_table[offset]))
        return ret

    def convert_to_python(self, offsets):
        """
        Convert one java offset or an iterable of java offsets to python offset/s

        Args:
          offsets: a single offset or an iterable of offsets

        Returns:
            the converted offset or offsets

        """
        return self._convert_from(offsets, from_table=self.java2python)

    def convert_to_java(self, offsets):
        """Convert one python offset or an iterable of python offsets to java offset/s

        Args:
          offsets: a single offset or an iterable of offsets

        Returns:
            the converted offset or offsets

        """
        return self._convert_from(offsets, from_table=self.python2java)
