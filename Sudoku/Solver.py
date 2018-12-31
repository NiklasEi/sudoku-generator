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
from .Board import Board


class Solver:
    """Brute force solver that tries every possible value for every empty square."""

    def __init__(self, board: Board):
        """Keeps a local copy of the given board, so it works non-destructively,
        and you can ask for the solution after asking whether it can be solved.
        """
        self.board = board.copy()
        self.empties = self.board.get_empty_cells()

    def is_solution(self):
        """Validate that every row, column, and tile in a solution contains all the possible values."""
        valid = set(range(1, self.board.side_length + 1))
        for tile in self.board.tiles:
            if set([cell.value for cell in tile]) != valid:
                return False
        for row in self.board.rows:
            if set([cell.value for cell in row]) != valid:
                return False
        for col in self.board.columns:
            if set([cell.value for cell in col]) != valid:
                return False
        return True

    def can_solve(self) -> bool:
        """Return whether the given board could be solved."""
        index = 0
        while -1 < index < len(self.empties):
            current = self.empties[index]
            possibles = self.board.get_possibles(current)
            untried = [val for val in range(current.value + 1, self.board.side_length + 1) if val in possibles]
            if untried:
                current.value = untried[0]
                index += 1
            else:
                index -= 1
        if index < 0:
            return False
        else:
            return self.is_solution()
