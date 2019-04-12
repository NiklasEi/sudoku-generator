# MIT License
#
# Copyright (c) 2018-2019 Daniel Brotsky
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
import json
import sys
import time

import click

from .board import Board
from .generator import Generator
from .norvig_solver import Solver


@click.group()
@click.pass_context
@click.option('-v', '--verbose', count=True,
              help="print puzzle details then content to stderr")
@click.option('-o', '--output', type=click.Choice(['json', 'html', 'ascii']),
              default='json', show_default=True,
              help="format for writing results to stdout")
def sudoku(ctx: click.Context, verbose: int, output: str):
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['output'] = output


@sudoku.command()
@click.option('-s', '--sidelen', type=click.Choice(["4", "9", "16"]),
              required=True,
              help="Desired puzzle side length (4, 9, or 16).")
@click.option('-d', '--difficulty',
              type=click.Choice(Generator.thresholds.keys()),
              default='easy', show_default=True,
              help="Desired difficulty of the generated puzzle.")
@click.option('-c', '--count', type=click.IntRange(min=1),
              default=1, show_default=True,
              help="How many puzzles to generate.")
@click.pass_context
def generate(ctx: click.Context, sidelen, difficulty, count):
    """Generate one or more Sudoku puzzles.
    You can specify the size and difficulty of the puzzles."""
    verbose = ctx.obj['verbose']
    output = ctx.obj['output']
    outputs = []
    gen = Generator(sidelen, difficulty)
    start = time.time()
    for iteration in range(1, count + 1):
        result = gen.generate_one()
        outputs.append(result)
    end = time.time()
    if output == 'json':
        print(json.dumps([dict(puzzle=result['puzzle'].values(),
                               solution=result['solution'].values())
                          for result in outputs]))
    else:
        for iteration, result in enumerate(outputs, 1):
            if output == 'html':
                print("Puzzle #{0}:\n{1}\nSolution #{0}:\n{2}\n"
                      .format(iteration, result['puzzle'].html(), result['solution'].html()), file=sys.stderr)
            elif output == 'ascii':
                print("Puzzle #{0}:\n{1}\nSolution #{0}:\n{2}\n"
                      .format(iteration, result['puzzle'].ascii(), result['solution'].ascii()), file=sys.stderr)
    if verbose:
        print("Summary statistics:", file=sys.stderr)
        puzzle_str = "puzzles that are" if count > 1 else "puzzle that is"
        print("Generated {3} '{0}' {2} {1}x{1}."
              .format(difficulty, sidelen, puzzle_str, count),
              file=sys.stderr)
        for index, result in enumerate(outputs, 1):
            board = result['puzzle']
            empty = len(board.get_empty_cells())
            filled = len(board.get_filled_cells())
            total = board.size
            print("Puzzle {}: Empty={} ({:.0%}), Filled={} ({:.0%})."
                  .format(index,
                          empty, empty / total,
                          filled, filled / total),
                  file=sys.stderr)
        print("Generation time: {:.1f} seconds total ({:.1f} secs/puzzle)."
              .format(end - start, (end - start) / count),
              file=sys.stderr)


@sudoku.command()
@click.argument('infile', type=click.File(), required=True)
@click.pass_context
def solve(ctx: click.Context, infile):
    """Solve the puzzle whose values are specified in INFILE (or - for stdin).
    The file format is whitespace-separated cell values, filled left-to-right top-to-bottom.
    You can use multiple lines in the file, one row per line, but linebreaks are not required.
    Each value is a digit 1-9/A-G. The puzzle size is inferred from the number of cells."
    """
    verbose = ctx.obj['verbose']
    output = ctx.obj['output']
    if infile is None:
        raise ValueError("You must specify a puzzle to solve.")
    board = Board.from_file(infile)
    if verbose:
        print("Puzzle before solving is:\n\n{}".format(board), file=sys.stderr)
    solver = Solver(board)
    if solver.can_solve():
        solution = solver.solution
        if verbose:
            print("Puzzle after solving is:\n\n{}".format(solution), file=sys.stderr)
        if output == 'html':
            print(solution.html())
        elif output == 'ascii':
            print(solution)
        else:
            print(json.dumps(dict(puzzle=board.values(), solution=solution.values())))
    else:
        raise ValueError("Puzzle cannot be solved")


if __name__ == '__main__':
    sudoku(obj={})
