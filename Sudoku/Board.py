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
from __future__ import annotations


class Board:
    """A Board is a Sudoku puzzle.  It contains cells organized into rows, columns, and
    _tiles_ (the sub-squares which also have to contain each possible value).  Cells
    are either _filled_ (with a value) or _empty_ (not yet filled); in this implementation
    we use a 0 as the value in an empty cell.  This implementation organizes puzzle cells
    left-to-right along each row, and the rows are read top-to-bottom.  Tiles are also
    organized in the same order.  The _rank_ of the puzzle is the number of squares
    along the edge of each tile, hence a 9x9 puzzle has a rank of 3.  Each horizontal
    collection of aligned tiles is called a _band_, and each vertical collection of
    aligned tiles is called a _stack_.
    """
    def __init__(self, rank: int = 3, numbers: [int] = None):
        """Create a board with the given rank and initial cell values.
        If you don't specify initial values then all cells will be empty.
        Basic range checking is done on the values to make sure that they
        match the shape of the puzzle, but it's possible to create boards
        with non-solvable context.
        """
        # validate arguments
        if rank not in [2, 3, 4]:
            raise ValueError("Rank must be 2, 3, or 4 (giving side length of 4, 9, or 16)")
        self.rank = rank
        self.side_length = rank * rank
        self.size = self.side_length * self.side_length
        if numbers:
            if len(numbers) != self.size:
                raise ValueError("You must specify a value for each square")
            if max(numbers) > self.side_length or min(numbers) < 0:
                raise ValueError("Each cell value must be in the range 0 to {}".format(self.side_length))
        else:
            numbers = [0] * self.size
        # create the indices
        self.rows = [[] for i in range(self.side_length)]
        self.columns = [[] for i in range(self.side_length)]
        self.tiles = [[] for i in range(self.side_length)]
        self.cells = []
        # create initialized cells and put them in their row, column and tile
        for row in range(0, self.side_length):
            for col in range(0, self.side_length):
                tile = self.rank * (row // self.rank) + (col // self.rank)
                cell = Cell(row, col, tile, numbers.pop(0))
                self.rows[row].append(cell)
                self.columns[col].append(cell)
                self.tiles[tile].append(cell)
                self.cells.append(cell)
        # for each cell, pre-compute its context (the cells in its row, column, or tile)
        for cell in self.cells:
            cell.context = self.get_context(cell)

    def get_filled_cells(self) -> [Cell]:
        """Return all the cells with values."""
        return [c for c in self.cells if c.value != 0]

    def get_empty_cells(self) -> [Cell]:
        """Return all the cells with no value."""
        return [c for c in self.cells if c.value == 0]

    def get_context(self, cell: Cell) -> {Cell}:
        """Return the set of cells that share a row, column or tile with this cell."""
        return {c for c in self.rows[cell.row] + self.columns[cell.col] + self.tiles[cell.tile] if c is not cell}

    def get_excluded(self, cell) -> {Cell}:
        """Return the set of values this cell *cannot* have (because of cells in its context)."""
        return {c.value for c in cell.context if c.value != 0}

    # get all the possible values for cell, that is, the complement of the excluded values
    def get_possibles(self, cell) -> {Cell}:
        """Return the set of values this cell *can* have (considering cells in its context)."""
        excluded = self.get_excluded(cell)
        return {c for c in range(1, self.side_length + 1) if c not in excluded}

    def get_density(self, cell) -> float:
        """Return the percentage of filled cells in this cell's context."""
        return len([x for x in cell.context if x.value != 0]) // len(cell.context)

    def swap_row_values(self, row1, row2, allow_different_tiles=False):
        """Swap the values of corresponding cells in the given rows.
        This is not solution-preserving if the rows are not in the same tile,
        so you have to specifically provide for that if that's what you want.
        """
        if not allow_different_tiles and row1 // self.rank != row2 // self.rank:
            raise ValueError('Swapping rows from different tiles is not solution-preserving.')
        rows = self.rows
        for col in range(0, len(self.rows[row2])):
            rows[row2][col].value, rows[row1][col].value = rows[row1][col].value, rows[row2][col].value

    def swap_column_values(self, col1, col2, allow_different_tiles=False):
        """Swap the values of corresponding cells in the given columns.
        This is not solution-preserving if the rows are not in the same tile,
        so you have to specifically provide for that if that's what you want.
        """
        if not allow_different_tiles and col1 // self.rank != col2 // self.rank:
            raise ValueError("Swapping rows from different tiles is not solution-preserving.")
        columns = self.columns
        for row in range(0, len(self.columns[col2])):
            columns[col2][row].value, columns[col1][row].value = columns[col1][row].value, columns[col2][row].value

    def swap_stack_values(self, stack1, stack2):
        """Swap the values of corresponding cells in all the tiles in the given stacks.
        (A _stack_ is a complete set of vertically-aligned tiles.)
        """
        for offset in range(0, self.rank):
            self.swap_column_values(stack1 * self.rank + offset, stack2 * self.rank + offset, True)

    def swap_band_values(self, band1, band2):
        """Swap the values of corresponding cells in all the tiles in the given bands.
        (A _band_ is a complete set of horizontally-aligned tiles.)
        """
        for offset in range(0, self.rank):
            self.swap_row_values(band1 * self.rank + offset, band2 * self.rank + offset, True)

    def copy(self) -> Board:
        """Return a deep copy of this board."""
        return Board(rank=self.rank, numbers=[c.value for c in self.cells])

    def dict(self):
        """Return a dictionary that can be used to recreate this board."""
        return {'rank': self.rank, 'values': [cell.value for cell in self.cells]}

    def html(self) -> str:
        """Return an HTML representation of this board."""
        html = "<table>"
        for row in self.rows:
            row_string = "<tr>"
            for cell in row:
                row_string += '<td align="center" style="text-align:center">' + str(cell) + '</td>'
            row_string += "</tr>"
            html += row_string
        html += "</table>"
        return html

    def ascii(self):
        """Return a human-readable ascii fixed-width representation of the board."""
        output = ''
        for row_num, row in enumerate(self.rows, 1):
            for col_num, cell in enumerate(row, 1):
                output += str(cell) + ' '
                if col_num < self.side_length:
                    if col_num % self.rank == 0:
                        output += '| '
                else:
                    output += '\n'
            if row_num < self.side_length:
                if row_num % self.rank == 0:
                    output += ('--' * self.rank + '+-') * (self.rank - 1)
                    output += '--' * self.rank + '\n'
        return output

    def __str__(self):
        """The printable form of a board is its ascii form."""
        return self.ascii()

    def __repr__(self):
        """The (almost) eval-able form of a board is its constructor (with its id for specificity)."""
        return '<Board(rank={rank},numbers={values}) at {id}>'.format(id=id(self),**self.dict())


class Cell:
    """Each cell in a Sudoku board has a row, a column, a tile, and a value.
    For convenience, a cell can be annotated with its _context_, which is
    all of the other cells in its row, column, and tile (so called because
    those are the cells that constrain its value)."""

    def __init__(self, row: int, col: int, tile: int, value: int = 0):
        """Each cell is initialized with its row, column, and tile.
        If a value is specified, that's remembered, otherwise the cell
        is initialized with a 0 value (meaning blank).  The context
        of each cell is initialized to empty; it is expected to be
        used as a cache by the board containing the cell.
        No error checking is done of any values.
        """
        self.row = row
        self.col = col
        self.tile = tile
        self.value = value
        self.context = []

    def __repr__(self):
        """The (almost) eval-able form of a cell is its constructor (with its id for specificity)."""
        return "<Cell(row={},col={},tile={},value={}) at {}>".format(self.row, self.col, self.tile, self.value,
                                                                     id(self))

    def __str__(self):
        """In traditional Sudoku, each cell is represented by its value as a single character.
        This implementation assumes a puzzle rank no bigger than 5 (so 25 as max cell value).
        """
        if self.value == 0:
            return "-"
        elif self.value < 10:
            return str(self.value)
        else:
            return chr(ord('A') + self.value - 10)
