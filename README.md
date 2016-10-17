# chrF
Reimplementation of the character-F evaluation measure for SMT

This implementation (c) Stig-Arne Grönroos 2016.

If you use the software for scientific purposes, please cite
> Popovic, Maja. (2015). ChrF: character n-gram F-score
> for automatic MT evaluation. EMNLP 2015, 392.





```
Command-line arguments:

positional arguments:
  hypothesis            Plain-text hypothesis file
  reference             Reference file. Can contain multiple alternatives,
                        split by --reference-separator

optional arguments:
  -h, --help            show this help message and exit

algorithm parameters:
  -n ORDER, --order ORDER
                        ngram order (default 6).
  -w NWEIGHT, --nweight NWEIGHT
                        comma separated ngram weights. (default uniform 1/n).
  -b BETA, --beta BETA  balance parameter for f-measure. (default 1.0).
  --ignore-space        Do not consider spaces as characters.

input options:
  --reference-separator SEP
                        Separator for multiple references (default "*#").

output options:
  --hide-precrec        Suppress precision and recall in summary.
  --show-ngram          Show n-gram level scores.
  --show-sentence       Show sentence level scores.
  --show-missing        Show ngrams without a match. Requires --show-sentence.
  --compatible          Produce backwards compatible output.

Simple usage example:

  chrF -b 2.0 hyp.txt ref.txt > score
```
