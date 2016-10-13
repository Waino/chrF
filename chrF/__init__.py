#!/usr/bin/env python3
# -*- coding: utf-8
"""
chrF - Reimplementation of the character-F evaluation measure for SMT
Popovic, Maja. (2015). ChrF: character n-gram F-score
for automatic MT evaluation. EMNLP 2015, 392.

This implementation (c) Stig-Arne Grönroos 2016.
"""

__version__ = '1.0.0'
__author__ = 'Stig-Arne Gronroos'
__author_email__ = "stig-arne.gronroos@aalto.fi"

from .measure import *
from . import cmd

