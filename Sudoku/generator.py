# MIT License
#
# Copyright (c) 2018-2019 Daniel Brotsky
#
# Portions copyright (c) 2018 Paul Rutledge
# (See https://github.com/RutledgePaulV/sudoku-generator)
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

from .board import Board
from .norvig_solver import Solver


class Generator:
    """Generate a problem puzzle by removing values from a solved puzzle,
    making sure that removal of the value doesn't introduce another solution.

    Before we start removing squares, we pick one of a small set of solved
    puzzles and preform a sequence of randomly-chosen, correctness-preserving
    transformations on it.  (Without this step, we would have to have a large
    number of solutions to generate a large number of puzzles.)

    We then pick squares whose values should be removed.  We do this
    in two sequences:

    First, we examine each square in the puzzle in a random sequence, and if
    the immediate neighbors of that square (row, column, and tile) constrain
    it completely, we remove its value.  The result of this step is always
    "easy" to solve, because there is always at least one square which can
    only have one value.

    Second, we take all the remaining squares that have values
    and we sort them from most-constrained to least-constrained (with
    random ordering where there are ties).  For each of these squares,
    we see if the puzzle can be solved with a different value in the
    square.  If not, we remove the square's value.

    The more squares we remove in each step, the harder the puzzle should be
    to solve.  But because the first few squares removed in the second step
    are most likely to be those who are completely constrained by their
    neighbors, stopping the first step before it has tried to remove values
    from every square means the second step will first try to complete the
    first step.
    """

    # fraction of single-valued and random squares to remove based on the difficulty level
    thresholds = {
        'easy': {'4': (6, 0), '9': (27, 0), '16': (64, 0)},
        'medium': {'4': (9, 1), '9': (41, 5), '16': (96, 16)},
        'hard': {'4': (12, 2), '9': (54, 10), '16': (128, 33)},
        'extreme': {'4': (16, 3), '9': (81, 15), '16': (184, 49)},
        'insane': {'4': (16, 4), '9': (81, 20), '16': (256, 66)}
    }
    # Starting solved boards of the supported sizes
    start_values = {
        "4": [[1, 2, 3, 4,
               3, 4, 1, 2,
               2, 3, 4, 1,
               4, 1, 2, 3],
              [1, 3, 2, 4,
               4, 2, 3, 1,
               2, 4, 1, 3,
               3, 1, 4, 2],
              [1, 4, 2, 3,
               3, 2, 4, 1,
               2, 3, 1, 4,
               4, 1, 3, 2],
              ],
        "9": [[1, 2, 3, 4, 5, 6, 7, 8, 9,
               4, 5, 6, 7, 8, 9, 1, 2, 3,
               7, 8, 9, 1, 2, 3, 4, 5, 6,
               2, 1, 4, 3, 6, 5, 8, 9, 7,
               3, 6, 5, 8, 9, 7, 2, 1, 4,
               8, 9, 7, 2, 1, 4, 3, 6, 5,
               5, 3, 1, 6, 4, 2, 9, 7, 8,
               6, 4, 2, 9, 7, 8, 5, 3, 1,
               9, 7, 8, 5, 3, 1, 6, 4, 2],
              [1, 3, 2, 4, 6, 5, 7, 9, 8,
               4, 6, 5, 7, 9, 8, 1, 3, 2,
               7, 9, 8, 1, 3, 2, 4, 6, 5,
               2, 4, 9, 5, 7, 3, 8, 1, 6,
               5, 7, 3, 8, 1, 6, 2, 4, 9,
               8, 1, 6, 2, 4, 9, 5, 7, 3,
               3, 5, 7, 6, 8, 1, 9, 2, 4,
               6, 8, 1, 9, 2, 4, 3, 5, 7,
               9, 2, 4, 3, 5, 7, 6, 8, 1],
              [9, 8, 7, 6, 5, 4, 3, 2, 1,
               6, 5, 4, 3, 2, 1, 9, 8, 7,
               3, 2, 1, 9, 8, 7, 6, 5, 4,
               8, 4, 3, 5, 1, 9, 2, 7, 6,
               5, 1, 9, 2, 7, 6, 8, 4, 3,
               2, 7, 6, 8, 4, 3, 5, 1, 9,
               7, 6, 2, 4, 3, 8, 1, 9, 5,
               4, 3, 8, 1, 9, 5, 7, 6, 2,
               1, 9, 5, 7, 6, 2, 4, 3, 8],
              ],
        "16": [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
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
                15, 16, 13, 14, 3, 4, 1, 2, 7, 8, 5, 6, 11, 12, 9, 10],
               ],
    }

    def __init__(self, side_length: str, difficulty: str):
        """The starting point for the generator must be a solvable puzzle."""
        self.board = None
        if side_length in self.start_values.keys():
            self.start_values_list = self.start_values[side_length]
            puzzle_size = int(side_length) * int(side_length)
        else:
            raise ValueError("Side length ({}) must be one of {}"
                             .format(side_length, self.start_values.keys()))
        if difficulty in self.thresholds.keys():
            thresholds = self.thresholds[difficulty][side_length]
            self.first_cutoff, self.second_cutoff = thresholds
        else:
            raise ValueError("Unknown difficulty level: {}".format(difficulty))

    def randomize(self, iterations):
        """Randomizes a random solution by doing swaps of rows and cols
        in a manner that preserves the Sudoku invariants.  Both the form of
        the swap and the rows/cols/bands/stacks to swap are chosen at random.
        """

        def random_two_in_rank() -> (int, int):
            """Pick two random values smaller than the rank of the board."""
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

    def remove_values_1(self, cutoff):
        """Do the first pass at removing values from cells.
        Pick up to cutoff cells at random. Then remove each cell's value if
        it's the only possible value for that cell.
        """
        cells = self.board.get_filled_cells()
        random.shuffle(cells)
        for cell in cells:
            if cutoff <= 0:
                return
            if len(self.board.get_possibles(cell)) == 1:
                cell.value = 0
                cutoff -= 1

    def reduce_pass_2(self, cutoff):
        """Do the second pass at removing values from cells.
        Pick up to cutoff cells sorted from highest to lowest density
        (breaking ties randomly).  Then remove each cell's value if doing so
        doesn't lead to another possible solution.
        """
        ranked_cells = [(x, self.board.get_density(x)) for x in
                        self.board.get_filled_cells()]
        random.shuffle(ranked_cells)
        cells = [x[0] for x in
                 sorted(ranked_cells, key=lambda x: x[1], reverse=True)]
        for cell in cells:
            if cutoff <= 0:
                return
            original = cell.value
            # for every other possible cell value, see if the board is solvable
            # if it is, then restore the original value so it isn't removed.
            for x in [val for val in self.board.get_possibles(cell)
                                     if val != original]:
                cell.value = x
                if Solver(self.board).can_solve():
                    cell.value = original
                    break
            if cell.value != original:
                cell.value = 0
                cutoff -= 1

    def generate_one(self) -> dict:
        """Generate a new puzzle and solution.
        The returned dictionary has a 'puzzle' entry and a 'solution' entry.
        """
        index = random.randrange(0, len(self.start_values_list))
        self.board = Board(self.start_values_list[index])
        if not Solver(self.board).is_solution():
            # Can't happen!  This is a program error.
            raise AssertionError("Board {} is not a solution!".format(index))
        self.randomize(self.board.size + 20)
        solution = self.board.copy()
        self.remove_values_1(self.first_cutoff)
        self.reduce_pass_2(self.second_cutoff)
        puzzle = self.board
        self.board = None
        return dict(puzzle=puzzle, solution=solution)
