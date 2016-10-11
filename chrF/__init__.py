#!/usr/bin/env python3
"""
chrF - Reimplementation of the character-F evaluation measure for SMT
Original by Maja Popovic
"""

import collections
import sys

Errors = collections.namedtuple('Errors',
    ['count', 'precrec', 'missing', 'reflen'])

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
    # space appended to treat last word equally to others
    # and for compatibility with original
    line += ' '
    if not use_space:
        line = line.replace(' ', '')
    max_n = min(max_n, len(line))
    result = []
    for n in range(1, max_n + 1):
        result.append(list(ngrams(line, n)))
    return result

def errors_n(hypothesis, reference):
    """Errors for a single length of n-gram"""
    errorcount = 0.0
    precrec = 0.0
    missing = []

    ref_counts = collections.Counter(reference)
    for ngram in hypothesis:
        if ref_counts[ngram] > 0:
            ref_counts[ngram] -= 1
        else:
            errorcount += 1.
            missing.append(ngram)

        if len(hypothesis) != 0:
            precrec = 100. * errorcount / len(hypothesis)
        else:
            if len(reference) != 0:
                precrec = 100
            else:
                precrec = 0.

    return Errors(errorcount, precrec, missing, len(reference))

def errors_multiref(hypothesis, references, max_n, use_space=True):
    """Yields errors in both directions,
    against the best matching of multiple references,
    for all ngram lengths up to max_n"""
    hyp_ngrams = ngrams_up_to(hypothesis, max_n, use_space=use_space)
    ref_ngrams = zip(*(ngrams_up_to(line, max_n, use_space=use_space)
                       for line in references))
    for (i, (hyp, refs)) in enumerate(zip(hyp_ngrams, ref_ngrams)):
        best_hyp_error = min((errors_n(hyp, ref) for ref in refs),
                             key=lambda x: x.precrec)
        best_ref_error = min((errors_n(ref, hyp) for ref in refs),
                             key=lambda x: x.precrec)
        yield (i, best_hyp_error, best_ref_error)

def print_missing_ngrams(n_sentences, side, i, error, out_separator):
    sys.stdout.write('{}::{}-{}grams: '.format(
        n_sentences, side, i + 1))
    sys.stdout.write(' '.join(
        out_separator.join(ngram)
        for ngram in error.missing))
    sys.stdout.write('\n')

def evaluate(hyp_lines, ref_lines, max_n,
             beta=1.0, ngram_weights=None,
             use_space=True, ref_separator='*#', out_separator='',
             print_missing=False, sentence_level=False, ngram_level=False):
    hyp_per = [0. for _ in range(max_n)]
    hyp_len = [0. for _ in range(max_n)]
    ref_per = [0. for _ in range(max_n)]
    ref_len = [0. for _ in range(max_n)]
    n_sentences = 0
    factor = beta ** 2

    if ngram_weights is None:
        ngram_weights = [1/float(max_n) for _ in range(max_n)]
    else:
        tot = sum(ngram_weights)
        ngram_weights = [float(w) / tot for w in ngram_weights]

    # FIXME: safe zip
    for (hyp_line, ref_line) in zip(hyp_lines, ref_lines):
        hyp_line = hyp_line.strip()
        ref_line = ref_line.strip()
        n_sentences += 1
        references = ref_line.split(ref_separator)
        sent_pre = [0. for _ in range(max_n)]
        sent_rec = [0. for _ in range(max_n)]
        sent_f = [0. for _ in range(max_n)]
        errors = errors_multiref(hyp_line, references,
                                 max_n, use_space=use_space)
        for (i, hyp_error, ref_error) in errors:
            hyp_per[i] += hyp_error.count
            hyp_len[i] += hyp_error.reflen
            ref_per[i] += ref_error.count
            ref_len[i] += ref_error.reflen

            if print_missing:
                print_missing_ngrams(n_sentences, 'ref', i, ref_error,
                                     out_separator)
                print_missing_ngrams(n_sentences, 'hyp', i, hyp_error,
                                     out_separator)

            if sentence_level:
                sent_pre[i] = 100 - ref_error.precrec
                sent_rec[i] = 100 - hyp_error.precrec
                if sent_pre[i] != 0 or sent_rec[i] != 0:
                    sent_f[i] = ((1 + factor) * sent_pre[i] * sent_rec[i]
                                 / (factor * sent_pre[i] + sent_rec[i]))
                else:
                    sent_f[i] = 0
                
                if ngram_level:
                    sys.stdout.write('{}::{}gram-{:6s}{:.4f}\n'.format(
                        n_sentences, i + 1, 'F', sent_f[i]))
                    sys.stdout.write('{}::{}gram-{:6s}{:.4f}\n'.format(
                        n_sentences, i + 1, 'Prec', sent_pre[i]))
                    sys.stdout.write('{}::{}gram-{:6s}{:.4f}\n'.format(
                        n_sentences, i + 1, 'Rec', sent_rec[i]))

        if sentence_level:
            sys.stdout.write('{}::chr{}-{}\t{:.4f}\n'.format(
                n_sentences, 'F', beta,
                sum(w * f for (w, f) in zip(ngram_weights, sent_f))))
            sys.stdout.write('{}::chr{}\t{:.4f}\n'.format(
                n_sentences, 'Prec', 
                sum(w * p for (w, p) in zip(ngram_weights, sent_pre))))
            sys.stdout.write('{}::chr{}\t{:.4f}\n'.format(
                n_sentences, 'Rec',
                sum(w * r for (w, r) in zip(ngram_weights, sent_rec))))

    tot_pre = [100 * (1 - (ref_per[i] / ref_len[i]))
               if ref_len[i] > 0 else 0
               for i in range(max_n)]
    tot_rec = [100 * (1 - (hyp_per[i] / hyp_len[i]))
               if hyp_len[i] > 0 else 0
               for i in range(max_n)]
    divisors = [(factor * tot_pre[i] + tot_rec[i]) for i in range(max_n)]
    tot_f = [(1 + factor) * tot_pre[i] * tot_rec[i] / divisors[i]
             if divisors[i] > 0 else 0
             for i in range(max_n)]

    if ngram_level:
        for i in range(max_n):
            sys.stdout.write('{}gram-{:6s}{:.4f}\n'.format(
                i + 1, 'F', tot_f[i]))
            sys.stdout.write('{}gram-{:6s}{:.4f}\n'.format(
                i + 1, 'Prec', tot_pre[i]))
            sys.stdout.write('{}gram-{:6s}{:.4f}\n'.format(
                i + 1, 'Rec', tot_rec[i]))

    sys.stdout.write('chr{}-{}\t{:.4f}\n'.format(
        'F', beta,
        sum(w * f for (w, f) in zip(ngram_weights, tot_f))))
    sys.stdout.write('chr{}\t{:.4f}\n'.format(
        'Prec', 
        sum(w * p for (w, p) in zip(ngram_weights, tot_pre))))
    sys.stdout.write('chr{}\t{:.4f}\n'.format(
        'Rec',
        sum(w * r for (w, r) in zip(ngram_weights, tot_rec))))


if __name__ == '__main__':
    with open('direct.plain', 'r') as hyp_lines:
        with open('ref.plain', 'r') as ref_lines:
            evaluate(hyp_lines,
                     ref_lines,
                     max_n=6,
                     beta=2.0,
                     ngram_weights=None,
                     use_space=True,
                     ref_separator='*#',
                     out_separator='==',
                     print_missing=True,
                     sentence_level=True,
                     ngram_level=True)
