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
import random

from .Board import Board
from .Solver import Solver


class Generator:
    """Generate a puzzle.  Puzzle generation is done by starting with a solved puzzle,
    performing a bunch of random (correctness-preserving) transformations on it, and
    then randomly deleting values from cells (as long as doing so would not allow
    for more than one solution)."""
    def __init__(self, rank=3, starting_file=None):
        """Generate a puzzle of the given rank (2, 3, or 4).  Since the new puzzle
        you end up with depends on the solved puzzle you start with, you can specify
        your own starting puzzle (in a file) rather than relying on the built-in one.

        If you supply a starting file, it should contain a puzzle's worth of cell
        values separated by whitespace, where each value is a single digit from
        1-4 for rank 2 puzzles, from 1-9 for rank 3 puzzles, and from 1-9 and A-G
        for rank 4 puzzles.  The values are inserted into the puzzle rows from left
        to right and top to bottom, and newlines are treated the same as any other
        whitespace, so it's easy to format the file using one line per row.  The
        puzzle in the file is checked to make sure it's a valid solved puzzle, so
        if you have any typos the construction will throw an error.
        """
        if starting_file:
            with open(starting_file) as f:
                numbers = [int(x, base=17) for x in f.read().split()]
            if len(numbers) == 16:
                rank = 2
            elif len(numbers) == 81:
                rank = 3
            elif len(numbers) == 256:
                rank = 4
            else:
                raise ValueError("Starter puzzle is not a valid Sudoku: it has {} cells?".format(len(numbers)))
        else:
            if rank == 2:
                numbers = [1, 2, 3, 4,
                           3, 4, 1, 2,
                           2, 3, 4, 1,
                           4, 1, 2, 3]
            elif rank == 3:
                numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9,
                           4, 5, 6, 7, 8, 9, 1, 2, 3,
                           7, 8, 9, 1, 2, 3, 4, 5, 6,
                           2, 1, 4, 3, 6, 5, 8, 9, 7,
                           3, 6, 5, 8, 9, 7, 2, 1, 4,
                           8, 9, 7, 2, 1, 4, 3, 6, 5,
                           5, 3, 1, 6, 4, 2, 9, 7, 8,
                           6, 4, 2, 9, 7, 8, 5, 3, 1,
                           9, 7, 8, 5, 3, 1, 6, 4, 2]
            elif rank == 4:
                numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
                           5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 1, 2, 3, 4,
                           9, 10, 11, 12, 13, 14, 15, 16, 1, 2, 3, 4, 5, 6, 7, 8,
                           13, 14, 15, 16, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
                           2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11, 14, 13, 16, 15,
                           6, 5, 8, 7, 10, 9, 12, 11, 14, 13, 16, 15, 2, 1, 4, 3,
                           10, 9, 12, 11, 14, 13, 16, 15, 2, 1, 4, 3, 6, 5, 8, 7,
                           14, 13, 16, 15, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11,
                           4, 3, 2, 1, 8, 7, 6, 5, 12, 11, 10, 9, 16, 15, 14, 13,
                           8, 7, 6, 5, 12, 11, 10, 9, 16, 15, 14, 13, 4, 3, 2, 1,
                           12, 11, 10, 9, 16, 15, 14, 13, 4, 3, 2, 1, 8, 7, 6, 5,
                           16, 15, 14, 13, 4, 3, 2, 1, 8, 7, 6, 5, 12, 11, 10, 9,
                           3, 4, 1, 2, 7, 8, 5, 6, 11, 12, 9, 10, 15, 16, 13, 14,
                           7, 8, 5, 6, 11, 12, 9, 10, 15, 16, 13, 14, 3, 4, 1, 2,
                           11, 12, 9, 10, 15, 16, 13, 14, 3, 4, 1, 2, 7, 8, 5, 6,
                           15, 16, 13, 14, 3, 4, 1, 2, 7, 8, 5, 6, 11, 12, 9, 10]
            else:
                raise ValueError('rank ({}) must be 2, 3, or 4.'.format(rank))
        # constructing board
        self.board = Board(rank, numbers)
        if not Solver(self.board).is_solution():
            raise ValueError('Starter puzzle is not a valid Sudoku:\n{}'.format(self.board))

    # function randomizes an existing complete puzzle
    def randomize(self, iterations):
        """Randomizes an existing complete puzzle by doing swaps of rows and cols
        in a manner that preserves the Sudoku invariants.  Both the form of
        the swap and the rows/cols/bands/stacks to swap are chosen at random.
        """
        if len(self.board.get_filled_cells()) != self.board.size:
            raise ValueError('Cannot randomize a partial board without compromising uniqueness.')

        def random_two_in_rank() -> (int, int):
            """Pick two values at random that are smaller than the rank"""
            possibles = list(range(0, self.board.rank))
            random.shuffle(possibles)
            return possibles[0], possibles[1]

        def random_tile_base() -> int:
            """Pick the base row/col of a tile at random."""
            return random.randrange(0, self.board.rank) * self.board.rank

        for x in range(0, iterations):
            case = random.randrange(0, 4)
            if case == 0:
                offset1, offset2 = random_two_in_rank()
                base = random_tile_base()
                self.board.swap_row_values(base + offset1, base + offset2)
            elif case == 1:
                offset1, offset2 = random_two_in_rank()
                base = random_tile_base()
                self.board.swap_column_values(base + offset1, base + offset2)
            elif case == 2:
                self.board.swap_stack_values(*random_two_in_rank())
            elif case == 3:
                self.board.swap_band_values(*random_two_in_rank())

    def reduce_via_logical(self, cutoff: int):
        """Remove up to percentage overall cells that can only have their current value"""
        if cutoff <= 0:
            return
        # pick used cells at random
        cells = self.board.get_filled_cells()
        random.shuffle(cells)
        # for each used cell, if it has only one possible value, remove that value
        for cell in cells:
            if len(self.board.get_possibles(cell)) == 1:
                cell.value = 0
                cutoff -= 1
                if cutoff == 0:
                    break

    def reduce_via_random(self, cutoff: int):
        """Remove up to percentage overall cells at random, as long as removal leaves us with a unique solution"""
        if cutoff <= 0:
            return
        # sort used cells by density heuristic, highest to lowest
        ranked_cells = [(x, self.board.get_density(x)) for x in self.board.get_filled_cells()]
        cells = [x[0] for x in sorted(ranked_cells, key=lambda x: x[1], reverse=True)]
        # for each used cell, try every other possible value to see if it leads to a solution
        # if not, then removing this value doesn't alter the unique solution, so remove it
        for cell in cells:
            original = cell.value
            others = [x for x in self.board.get_possibles(cell) if x != original]
            for x in others:
                cell.value = x
                if Solver(self.board).can_solve():
                    cell.value = original
                    break
            if cell.value != original:
                cell.value = 0
                cutoff -= 1
                if cutoff == 0:
                    break

    def _print_current_state(self):
        """Debugging aid meant for use while cells are having their values removed."""
        count, size = len(self.board.get_empty_cells()), self.board.size
        print("There are currently {}/{} vacant cells ({0:.0%}):\n{}".format(count, size, count/size), self.board)
