#!/usr/bin/env python3
"""
chrF - Reimplementation of the character-F evaluation measure for SMT
Original by Maja Popovic
"""

import collections
import itertools
import sys

Errors = collections.namedtuple('Errors',
    ['count', 'precrec', 'missing', 'hyplen', 'reflen'])

#__all__ = []

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
    use_n = min(max_n, len(line))
    result = []
    for n in range(1, use_n + 1):
        result.append(list(ngrams(line, n)))
    for _ in range(max_n - use_n):
        # empty lists for too long n-grams
        result.append([])
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

    return Errors(errorcount, precrec, missing,
                  len(hypothesis), len(reference))

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

def print_missing_ngrams(n_sentences, side, i, missing, compatible=False):
    sys.stdout.write('{}::{}-{}grams: '.format(
        n_sentences, side, i + 1))
    if compatible:
        # output compatible with original implementation
        sys.stdout.write(' '.join(
            '=='.join(ngram).replace(' ', '=')
            for ngram in missing))
        sys.stdout.write(' ')
    else:
        sys.stdout.write(' '.join(
            ''.join(ngram)
            for ngram in missing))
    sys.stdout.write('\n')

class Stats(object):
    def __init__(self, max_n):
        self.max_n = max_n
        self.hyp_err = [0. for _ in range(max_n)]
        self.hyp_len = [0. for _ in range(max_n)]
        self.hyp_missing = [list() for _ in range(max_n)]
        self.ref_err = [0. for _ in range(max_n)]
        self.ref_len = [0. for _ in range(max_n)]
        self.ref_missing = [list() for _ in range(max_n)]

    def __iadd__(self, other):
        for i in range(self.max_n):
            self.hyp_err[i] += other.hyp_err[i]
            self.hyp_len[i] += other.hyp_len[i]
            self.ref_err[i] += other.ref_err[i]
            self.ref_len[i] += other.ref_len[i]
        self.hyp_missing = None     # not aggregated
        self.ref_missing = None     # not aggregated
        return self

    def ngram_prf(self, factor):
        pre = [100 - (100 * (self.hyp_err[i] / self.hyp_len[i]))
               if self.hyp_len[i] > 0 else 0
               for i in range(self.max_n)]
        rec = [100 - (100 * (self.ref_err[i] / self.ref_len[i]))
               if self.ref_len[i] > 0 else 0
               for i in range(self.max_n)]
        divisors = [(factor * pre[i] + rec[i]) for i in range(self.max_n)]
        f = [(1 + factor) * pre[i] * rec[i] / divisors[i]
             if divisors[i] > 0 else 0
             for i in range(self.max_n)]

        return (pre, rec, f)

def apply_ngram_weights(pres, recs, fs, ngram_weights):
    pre = sum(w * p for (w, p) in zip(ngram_weights, pres))
    rec = sum(w * r for (w, r) in zip(ngram_weights, recs))
    f   = sum(w * f for (w, f) in zip(ngram_weights, fs))
    return (pre, rec, f)

def evaluate_single(hypothesis, references, max_n, factor,
                    use_space=True, ref_separator='*#'):
    stats = Stats(max_n)
    errors = errors_multiref(hypothesis, references,
                             max_n, use_space=use_space)
    for (i, hyp_error, ref_error) in errors:
        # in both cases .hyplen is correct
        # hyplen is a misnomer: should be "length used for normalization"
        stats.hyp_err[i] = hyp_error.count
        stats.hyp_len[i] = hyp_error.hyplen
        stats.ref_err[i] = ref_error.count
        stats.ref_len[i] = ref_error.hyplen
        stats.hyp_missing[i] = hyp_error.missing
        stats.ref_missing[i] = ref_error.missing
    return stats


def print_single(stats, line_n, beta, ngram_weights,
                 print_missing, sentence_level, ngram_level, compatible):
    factor = beta ** 2
    if print_missing:
        for i in range(stats.max_n):
            print_missing_ngrams(line_n, 'ref', i, stats.ref_missing[i],
                                 compatible)
        for i in range(stats.max_n):
            print_missing_ngrams(line_n, 'hyp', i, stats.hyp_missing[i],
                                 compatible)

    pres, recs, fs = stats.ngram_prf(factor)
    if ngram_level:
        for i in range(stats.max_n):
            sys.stdout.write('{}::{}gram-{:6s}{:.4f}\n'.format(
                line_n, i + 1, 'F', fs[i]))
            sys.stdout.write('{}::{}gram-{:6s}{:.4f}\n'.format(
                line_n, i + 1, 'Prec', pres[i]))
            sys.stdout.write('{}::{}gram-{:6s}{:.4f}\n'.format(
                line_n, i + 1, 'Rec', recs[i]))
            
    if sentence_level:
        pre, rec, f = apply_ngram_weights(pres, recs, fs, ngram_weights)
        sys.stdout.write('{}::chr{}-{}\t{:.4f}\n'.format(
            line_n, 'F', beta, f))
        sys.stdout.write('{}::chr{}\t{:.4f}\n'.format(
            line_n, 'Prec', pre))
        sys.stdout.write('{}::chr{}\t{:.4f}\n'.format(
            line_n, 'Rec', rec))

def print_summary(stats, beta, ngram_weights,
                  ngram_level=False, hide_precrec=False):
    factor = beta ** 2
    tot_pre, tot_rec, tot_f = stats.ngram_prf(factor)
    if ngram_level:
        for i in range(stats.max_n):
            sys.stdout.write('{}gram-{:6s}{:.4f}\n'.format(
                i + 1, 'F', tot_f[i]))
            sys.stdout.write('{}gram-{:6s}{:.4f}\n'.format(
                i + 1, 'Prec', tot_pre[i]))
            sys.stdout.write('{}gram-{:6s}{:.4f}\n'.format(
                i + 1, 'Rec', tot_rec[i]))

    pre, rec, f = apply_ngram_weights(tot_pre, tot_rec, tot_f, ngram_weights)
    sys.stdout.write('chr{}-{}\t{:.4f}\n'.format(
        'F', beta, f))
    if not hide_precrec:
        sys.stdout.write('chr{}\t{:.4f}\n'.format(
            'Prec', pre))
        sys.stdout.write('chr{}\t{:.4f}\n'.format(
            'Rec', rec))


def evaluate(hyp_lines,
             ref_tuples,
             max_n,
             beta=1.0,
             ngram_weights=None,
             use_space=True,
             summary=True,
             hide_precrec=False,
             print_missing=False,
             sentence_level=False,
             ngram_level=False,
             compatible=False):
    n_sentences = 0
    factor = beta ** 2
    tot_stats = Stats(max_n)

    if ngram_weights is None:
        ngram_weights = [1/float(max_n) for _ in range(max_n)]
    else:
        tot = sum(ngram_weights)
        ngram_weights = [float(w) / tot for w in ngram_weights]

    for (hyp_line, refs) in safe_zip(hyp_lines, ref_tuples):
        n_sentences += 1
        sent_stats = evaluate_single(
            hyp_line,
            refs,
            max_n,
            factor,
            use_space=use_space)
        tot_stats += sent_stats
        if sentence_level:
            print_single(sent_stats,
                         n_sentences,
                         beta,
                         ngram_weights,
                         print_missing=print_missing,
                         sentence_level=sentence_level,
                         ngram_level=ngram_level,
                         compatible=compatible)

    if summary:
        print_summary(tot_stats, beta, ngram_weights,
                      ngram_level, hide_precrec)
    return tot_stats


def safe_zip(*iterables):
    iters = [iter(x) for x in iterables]
    sentinel = object()
    for (j, tpl) in enumerate(itertools.zip_longest(*iterables, fillvalue=sentinel)):
        for (i, val) in enumerate(tpl):
            if val is sentinel:
                raise ValueError('Input {} was too short. '
                    'Row {} (and later) missing.'.format(i, j))
        yield tpl
