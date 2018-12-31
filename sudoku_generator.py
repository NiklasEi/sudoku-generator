# MIT License
#
# Copyright (c) 2018 Paul Rutledge and Daniel Brotsky
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import sys
import json
import click
from collections import namedtuple

from Sudoku.Generator import Generator

# setting thresholds and their cutoffs for each can_solve method
Threshold = namedtuple('Threshold', 'logical random')
thresholds = {
    'easy': Threshold(0.44, 0.0),
    'medium': Threshold(0.8, 0.065),
    'hard': Threshold(1.0, 0.13),
    'extreme': Threshold(1.0, 0.195),
    'insane': Threshold(1.0, 0.26),
}


@click.command()
@click.option('-r', '--rank', type=click.IntRange(min=2, max=4), default=3, show_default=True,
              help="square root of side length (2, 3, or 4)")
@click.option('-d', '--difficulty', type=click.Choice(thresholds.keys()), default='easy', show_default=True,
              help="desired difficulty of the generated puzzle")
@click.option('-c', '--count', default=1, show_default=True,
              help="how many puzzles to generate")
@click.option('-o', '--output', type=click.Choice(['json', 'html', 'none']), default='json', show_default=True,
              help="Whether to produce json, html, or no output")
@click.option('-v', '--verbose', is_flag=True,
              help="show generation details and final puzzle")
@click.option('--starter', type=click.Path(exists=True, dir_okay=False),
              help="Start from complete puzzle found in FILE "
                   "(format is space-separated cell values, one row per line)")
def generate(rank, difficulty, count, output, verbose, starter):
    outputs = []
    for iteration in range(1, count + 1):
        # create a starter solution and then randomize it
        gen = Generator(rank, starter)
        gen.randomize(gen.board.size + 20)
        # remove some single-valued squares, then randomly look for other squares
        initial = gen.board.copy()
        gen.reduce_via_logical(thresholds[difficulty].logical)
        gen.reduce_via_random(thresholds[difficulty].random)
        final = gen.board.copy()
        outputs.append(final.dict())
        if verbose:
            print("Solution {} before removals was:\n\n{}".format(iteration, initial), file=sys.stderr)
            print("Solution {} after removals is:\n\n{}".format(iteration, final), file=sys.stderr)
        if output == 'html':
            print(final.html())
    if output == 'json':
        if count == 1:
            print(json.dumps(outputs[0]))
        else:
            print(json.dumps(outputs))


if __name__ == '__main__':
    generate()
