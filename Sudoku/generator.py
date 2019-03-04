# MIT License
#
# Copyright (c) 2018-2019 Daniel Brotsky
#
# Portions copyright (c) 2018 Paul Rutledge at https://github.com/RutledgePaulV/sudoku-generator
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
    """Generate a puzzle.  Puzzle generation is done by starting with a solved puzzle,
    performing a bunch of random (correctness-preserving) transformations on it, and
    then randomly deleting values from cells (as long as doing so would not allow
    for more than one solution)."""

    # fraction of single-valued and random squares to remove based on the difficulty level
    thresholds = {
        'easy': (0.34, 0.0),
        'medium': (0.34, 0.065),
        'hard': (0.34, 0.13),
        'extreme': (0.34, 0.195),
        'insane': (0.34, 0.26),
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
               ]
    }

    def __init__(self, side_length: str, difficulty: str):
        """The starting point for the generator must be a solvable puzzle."""
        self.board = None
        if side_length in self.start_values.keys():
            self.start_values_list = self.start_values[side_length]
            puzzle_size = int(side_length) * int(side_length)
        else:
            raise ValueError("Side length ({}) must be one of {}".format(side_length, self.start_values.keys()))
        if difficulty in self.thresholds.keys():
            self.single_value_threshold, self.random_threshold = self.thresholds[difficulty]
        else:
            raise ValueError("Unknown difficulty level: {}".format(difficulty))
        self.single_value_cutoff = int(self.single_value_threshold * puzzle_size)
        self.random_cutoff = int(self.random_threshold * puzzle_size)

    def randomize(self, iterations):
        """Randomizes a random solution by doing swaps of rows and cols
        in a manner that preserves the Sudoku invariants.  Both the form of
        the swap and the rows/cols/bands/stacks to swap are chosen at random.
        """
        def random_two_in_rank() -> (int, int):
            """Pick two values at random that are smaller than the side_length"""
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

    def reduce_via_logical(self):
        """Remove up to percentage overall cells that can only have their current value"""
        cutoff = self.single_value_cutoff
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

    def reduce_via_random(self):
        """Remove up to percentage overall cells at random, as long as removal leaves us with a unique solution"""
        cutoff = self.random_cutoff
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

    def generate_one(self) -> dict:
        """Generate a new puzzle and solution.
        The returned dictionary has a 'puzzle' entry and a 'solution' entry.
        """
        self.board = Board(self.start_values_list[random.randrange(0, len(self.start_values_list))])
        if not Solver(self.board).is_solution():
            raise ValueError("Starting board is not a solution:\n{}".format(self.board.ascii()))
        self.randomize(self.board.size + 20)
        solution = self.board.copy()
        self.reduce_via_logical()
        self.reduce_via_random()
        puzzle = self.board
        self.board = None
        return dict(puzzle=puzzle, solution=solution)
