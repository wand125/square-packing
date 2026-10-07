import Sqtri.Check

namespace SquarePacking.Tri.N3

def L : Q3 := q (3/2 : ℚ) 1
def yTop : Q3 := q (3/2 : ℚ) (3/4 : ℚ)
def pts : List Pt := [(q 1 (1/3 : ℚ), q 0 (1/2 : ℚ), (1/3 : ℚ)), (q (1/4 : ℚ) (5/6 : ℚ), q (1/2 : ℚ) (1/4 : ℚ), (1/3 : ℚ)), (q (1/2 : ℚ) (2/3 : ℚ), q 0 (1/2 : ℚ), (1/3 : ℚ)), (q 1 (1/3 : ℚ), q 1 0, (1/3 : ℚ)), (q (5/4 : ℚ) (1/6 : ℚ), q (1/2 : ℚ) (1/4 : ℚ), (1/3 : ℚ)), (q (1/2 : ℚ) (2/3 : ℚ), q 1 0, (1/3 : ℚ)), (q (3/4 : ℚ) (1/2 : ℚ), q (1/2 : ℚ) (1/4 : ℚ), (1/3 : ℚ))]

theorem weights : weightsOk pts = true := by decide +kernel

end SquarePacking.Tri.N3
