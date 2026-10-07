import Sqtri.Check

namespace SquarePacking.Tri.M4

def L : Q3 := q 4 (2/3 : ℚ)
def yTop : Q3 := q 1 2
def pts : List Pt := [(q 1 (1/3 : ℚ), q (1/3 : ℚ) (1/3 : ℚ), 1), (q 2 (1/3 : ℚ), q (1/3 : ℚ) (1/3 : ℚ), 1), (q 3 (1/3 : ℚ), q (1/3 : ℚ) (1/3 : ℚ), 1), (q (3/2 : ℚ) (1/3 : ℚ), q (1/3 : ℚ) (5/6 : ℚ), 1), (q (5/2 : ℚ) (1/3 : ℚ), q (1/3 : ℚ) (5/6 : ℚ), 1), (q 2 (1/3 : ℚ), q (1/3 : ℚ) (4/3 : ℚ), 1)]

theorem weights : weightsOk pts = true := by decide +kernel

end SquarePacking.Tri.M4
