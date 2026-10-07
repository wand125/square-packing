import Sqtri.Check

namespace SquarePacking.Tri.N4

def L : Q3 := q 3 (2/3 : ℚ)
def yTop : Q3 := q 1 (3/2 : ℚ)
def pts : List Pt := [(q 1 (1/3 : ℚ), q (1/3 : ℚ) (1/3 : ℚ), 1), (q 2 (1/3 : ℚ), q (1/3 : ℚ) (1/3 : ℚ), 1), (q (3/2 : ℚ) (1/3 : ℚ), q (1/3 : ℚ) (5/6 : ℚ), 1)]

theorem weights : weightsOk pts = true := by decide +kernel

end SquarePacking.Tri.N4
