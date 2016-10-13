# -*- coding: utf-8
import sys
import argparse

from .measure import evaluate

def get_argparser():
    parser = argparse.ArgumentParser(
        description="""
chrF 1.0.0

Copyright (c) 2016, Stig-Arne Grönroos
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1.  Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

2.  Redistributions in binary form must reproduce the above
    copyright notice, this list of conditions and the following
    disclaimer in the documentation and/or other materials provided
    with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

Command-line arguments:
""",
        epilog="""
Simple usage example:

  %(prog)s -b 2.0 hyp.txt ref.txt > score

""",
        formatter_class=argparse.RawDescriptionHelpFormatter)

    add_arg = parser.add_argument
    add_arg('hypothesis', help='Plain-text hypothesis file')
    add_arg('reference',
        help='Reference file. '
             'Can contain multiple alternatives, '
             'split by --reference-separator')
    
    add_arg = parser.add_argument_group(
        'algorithm parameters').add_argument
    add_arg('-n', '--order', type=int, default=6,
            help='ngram order (default %(default)s).')
    add_arg('-w', '--nweight', default=None,
            help='comma separated ngram weights. '
                 '(default uniform 1/n).')
    add_arg('-b', '--beta', type=float, default=1.0,
            help='balance parameter for f-measure. '
                 '(default %(default)s).')
    add_arg('--ignore-space', default=False, action='store_true',
            help='Do not consider spaces as characters.')

    add_arg = parser.add_argument_group(
        'input options').add_argument
    add_arg('--reference-separator', dest='refsep',
            default='*#', metavar='SEP',
            help='Separator for multiple references '
                 '(default "%(default)s").')

    add_arg = parser.add_argument_group(
        'output options').add_argument
    add_arg('--hide-precrec', default=False, action='store_true',
            help='Suppress precision and recall in summary.')
    add_arg('--show-ngram', dest='ngram_level',
            default=False, action='store_true',
            help='Show n-gram level scores.')
    add_arg('--show-sentence', dest='sent_level',
            default=False, action='store_true',
            help='Show sentence level scores.')
    add_arg('--show-missing', dest='missing',
            default=False, action='store_true',
            help='Show ngrams without a match. '
                 'Requires --show-sentence.')
    add_arg('--compatible', default=False, action='store_true',
            help='Produce backwards compatible output.')

    return parser

def main(args):
    if args.nweight is None:
        ngram_weights = None
    else:
        ngram_weights = args.nweight.split(',')

    with open(args.hypothesis, 'r') as hyp_lines:
        with open(args.reference, 'r') as ref_lines:
            hyp_lines = (line.strip() for line in hyp_lines)
            ref_lines = (line.strip().split(args.refsep)
                         for line in ref_lines)
            stats = evaluate(
                hyp_lines,
                ref_lines,
                max_n=args.order,
                beta=args.beta,
                ngram_weights=ngram_weights,
                use_space=not args.ignore_space,
                hide_precrec=args.hide_precrec,
                print_missing=args.missing,
                sentence_level=args.sent_level,
                ngram_level=args.ngram_level,
                compatible=args.compatible)
