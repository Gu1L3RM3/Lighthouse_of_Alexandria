from __future__ import annotations

from collections.abc import Sequence


# Pivots below this are treated as zero (singular system).
SINGULAR_TOLERANCE = 1e-12


class SingularMatrixError(ValueError):
    pass


def solve_linear_system(matrix: Sequence[Sequence[float]], rhs: Sequence[float]) -> list[float]:
    """Solve ``matrix @ x = rhs`` by Gaussian elimination with partial pivoting.

    Circuit matrices have a handful of nodes, so pure Python keeps the build
    free of numpy without a measurable cost.
    """
    size = len(rhs)
    augmented = [[float(value) for value in row] + [float(rhs[index])] for index, row in enumerate(matrix)]

    for column in range(size):
        pivot_row = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot_row][column]) < SINGULAR_TOLERANCE:
            raise SingularMatrixError("Matrix is singular")
        augmented[column], augmented[pivot_row] = augmented[pivot_row], augmented[column]

        pivot = augmented[column]
        for row in range(column + 1, size):
            factor = augmented[row][column] / pivot[column]
            if factor:
                target = augmented[row]
                for index in range(column, size + 1):
                    target[index] -= factor * pivot[index]

    values = [0.0] * size
    for row in reversed(range(size)):
        accumulated = sum(augmented[row][index] * values[index] for index in range(row + 1, size))
        values[row] = (augmented[row][size] - accumulated) / augmented[row][row]
    return values
