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
import time
import json
import click
from collections import namedtuple

from .Generator import Generator
from .Board import Board
from .Solver import Solver

# Thresholds that define the difficulty levels
Threshold = namedtuple('Threshold', 'logical random')
thresholds = {
    'easy': Threshold(0.34, 0.0),
    'medium': Threshold(0.34, 0.065),
    'hard': Threshold(0.34, 0.13),
    'extreme': Threshold(0.40, 0.195),
    'insane': Threshold(0.40, 0.26),
}


@click.group(chain=True)
@click.pass_context
@click.option('-v', '--verbose', count=True,
              help="print puzzle details then content to stderr")
@click.option('-o', '--output', type=click.Choice(['json', 'html', 'ascii']), default='json', show_default=True,
              help="format for writing puzzles to stdout")
def sudoku(ctx: click.Context, verbose: int, output: str):
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['output'] = output

@sudoku.command()
@click.option('-r', '--rank', type=click.IntRange(min=2, max=4), default=3, show_default=True,
              help="square root of side length (2, 3, or 4)")
@click.option('-d', '--difficulty', type=click.Choice(thresholds.keys()), default='easy', show_default=True,
              help="desired difficulty of the generated puzzle")
@click.option('-c', '--count', default=1, show_default=True,
              help="how many puzzles to generate")
@click.option('--starter', type=click.Path(exists=True, dir_okay=False),
              help="Start from complete puzzle found in a file. "
                   "The file format is whitespace-separated cell values, read left-to-right top-to-bottom. "
                   "You can use multiple lines, one row per line, but linebreaks are not required. "
                   "The rank is inferred from the number of cells.")
@click.pass_context
def generate(ctx: click.Context, rank, difficulty, count, starter):
    """Generate one or more Sudoku puzzles.
    You can specify the size and difficulty of the puzzles."""
    verbose = ctx.obj['verbose']
    output = ctx.obj['output']
    outputs = []
    logical, random = thresholds[difficulty].logical, thresholds[difficulty].random
    start = time.time()
    for iteration in range(1, count + 1):
        gen = Generator(rank, starter)
        if verbose >= iteration:
            print("Request {0} is for '{3}' rank {1} ({2}x{2}).  Randomizing solution..."
                  .format(iteration, gen.board.rank, gen.board.side_length, difficulty), file=sys.stderr)
        gen.randomize(gen.board.size + 20)
        initial = gen.board.copy()
        if verbose > iteration:
            print("Solution puzzle {}:\n\n{}".format(iteration, initial), file=sys.stderr)
        logical_cutoff, random_cutoff = int(logical * initial.size), int(random * initial.size)
        if verbose >= iteration:
            print("Removing up to {} fully-constrained values {:.0%}..."
                  .format(logical_cutoff, logical), file=sys.stderr)
        gen.reduce_via_logical(logical_cutoff)
        if verbose >= iteration:
            print("Removing up to {} randomly-chosen values {:.0%}..."
                  .format(random_cutoff, random), file=sys.stderr)
        gen.reduce_via_random(random_cutoff)
        final = gen.board.copy()
        outputs.append(final)
        if verbose >= iteration:
            print("Removed a total of {} values; {} values remain in puzzle."
                  .format(len(final.get_empty_cells()), len(final.get_filled_cells())), file=sys.stderr)
        if verbose > iteration:
            print("Generated puzzle {}:\n\n{}".format(iteration, final), file=sys.stderr)
        if output == 'html':
            print(final.html())
        elif output == 'ascii':
            print(final.ascii())
    end = time.time()
    ctx.obj['outputs'] = outputs
    if output == 'json':
        print(json.dumps([board.dict() for board in outputs]))
    if verbose and count > 1:
        print("Summary statistics:", file=sys.stderr)
        for index, board in enumerate(outputs, 1):
            empty, filled, total = len(board.get_empty_cells()), len(board.get_filled_cells()), board.size
            print("Puzzle {}: Empty={} ({:.0%}), Filled={} ({:.0%})."
                  .format(index, empty, empty/total, filled, filled/total), file=sys.stderr)
        print("Generation time: {:.1f} seconds total (average {:.1f} seconds per puzzle)."
              .format(end - start, (end - start) / count), file=sys.stderr)

@sudoku.command()
@click.argument('infile', type=click.File('r'), required=False)
@click.pass_context
def solve(ctx: click.Context, infile):
    """Solve one or more Sudoku puzzles.
    Optional INFILE (or - for stdin) contains puzzles in JSON format, as produced by
    the generator. If no input file is specified, and this command follows a generate
    command, then the puzzles produced by the generator are used as the input.
    """
    verbose = ctx.obj['verbose']
    output = ctx.obj['output']
    if input is None:
        inputs = ctx.obj['outputs']
    else:
        inputs = json.load(infile)
    outputs = []
    for index, puzzle in enumerate(inputs, 1):
        if not isinstance(puzzle, dict) or 'rank' not in puzzle or 'values' not in puzzle:
            raise ValueError("Not a valid puzzle specification: {}".format(puzzle))
        board = Board(puzzle['rank'], puzzle['values'])
        if verbose:
            print("Puzzle {} before solving was:\n\n{}".format(index, board), file=sys.stderr)
        solver = Solver(board)
        if solver.can_solve():
            solution = solver.board
            outputs.append(solution.dict())
            if verbose:
                print("Puzzle {} after solving is:\n\n{}".format(index, solution), file=sys.stderr)
            if output == 'html':
                print(solution)
            elif output == 'ascii':
                print(solution)
        else:
            outputs.append(board.dict())
            if verbose:
                print("Puzzle {} has no solution.".format(index), file=sys.stderr)
    if output == 'json':
        print(json.dumps(outputs))


if __name__ == '__main__':
    sudoku(obj={})
