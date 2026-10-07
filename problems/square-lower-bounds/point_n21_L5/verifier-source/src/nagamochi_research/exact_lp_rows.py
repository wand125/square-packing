"""Exact column sums, skipping zero entries in otherwise dense LP rows."""
from fractions import Fraction as F


def weighted_columns(A,ids,weights):
    result=[F(0)]*len(A[0])
    for i,y in zip(ids,weights):
        if not y:continue
        for j,a in enumerate(A[i]):
            if a:result[j]+=a*y
    return result
