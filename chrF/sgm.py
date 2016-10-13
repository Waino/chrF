import collections
import itertools
import re

from .measure import evaluate

RE_DOC = re.compile(r'<doc sysid="([^"]*)" docid="([^"]*)" [^>]*>')
RE_SEG = re.compile(r'<seg id="([^"]*)">(.*)</seg>')

Segment = collections.namedtuple('Segment',
    ['sysid', 'docid', 'segid', 'text'])

def read_sgm(lines):
    docid = None
    sysid = None
    for line in lines:
        line = line.strip()
        m = RE_DOC.match(line)
        if m:
            sysid, docid = m.groups()
            continue
        m = RE_SEG.match(line)
        if m:
            segid, text = m.groups()
            yield Segment(sysid, docid, segid, text)


def index_refs(segments):
    refs_by_id = collections.defaultdict(list)
    for seg in segments:
        refs_by_id[(seg.docid, seg.segid)].append(seg.text)
    return refs_by_id


def form_pairs(hyp_segs, ref_dict):
    hyp_segs, hyp_segs2 = itertools.tee(hyp_segs)
    hyps = (seg.text for seg in hyp_segs)
    refs = (ref_dict[(seg.docid, seg.segid)] for seg in hyp_segs2)
    return hyps, refs


def sgm_main(args):
    if args.nweight is None:
        ngram_weights = None
    else:
        ngram_weights = args.nweight.split(',')

    with open(args.hypothesis, 'r') as hyp_lines:
        with open(args.reference, 'r') as ref_lines:
            hyp_segs = read_sgm(hyp_lines)
            ref_dict = index_refs(read_sgm(ref_lines))
            hyps, refs = form_pairs(hyp_segs, ref_dict)
            stats = evaluate(
                hyps,
                refs,
                max_n=args.order,
                beta=args.beta,
                ngram_weights=ngram_weights,
                use_space=not args.ignore_space,
                hide_precrec=args.hide_precrec,
                print_missing=args.missing,
                sentence_level=args.sent_level,
                ngram_level=args.ngram_level,
                compatible=args.compatible)
