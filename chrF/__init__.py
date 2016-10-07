#!/usr/bin/env python
"""
chrF - Reimplementation of the character-F evaluation measure for SMT
Original by Maja Popovic
"""

import collections

#__all__ = []

__version__ = '0.0.1'
__author__ = 'Stig-Arne Gronroos'
__author_email__ = "stig-arne.gronroos@aalto.fi"

#_logger = logging.getLogger(__name__)

def ngrams(line, n):
    """Yields ngrams of length exactly n."""
    offsets = [line[i:] for i in range(n)]
    for ngram in zip(*offsets):
        yield ngram

def ngrams_up_to(line, max_n, use_space=True):
    """Yields all character n-grams of lengths from 1 to max_n.
    If use_space is False, spaces are not counted as chars."""
    if not use_space:
        line = line.replace(' ', '')
    max_n = min(max_n, len(line))
    result = []
    for n in range(1, max_n + 1):
        result.append(list(ngrams(line, n)))
    return result

def errors(hypothesis, reference):
    errorcount = 0.0
    precrec = 0.0
    missing = []

    ref_counts = collections.Counter(reference)
    for ngram in hypothesis:
        if ref_counts[ngram] > 0:
            ref_counts[ngram] -= 1
        else:
            errorcount += 1
            missing.append(ngram)

        if len(hypothesis) != 0:
            precrec = 100 * errorcount / len(hypothesis)
        else:
            if len(reference) != 0:
                precrec = 100
            else:
                precrec = 0

    return errorcount, precrec, missing

