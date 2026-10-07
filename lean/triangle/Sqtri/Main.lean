import Sqtri.Upper
import Sqtri.Data.N2.All
import Sqtri.Data.N3.All
import Sqtri.Data.N4.All

/-!
# The smallest equilateral triangles holding 2, 3 and 4 unit squares

* `minSideTri_two   : minSideTri 2 = 2 + 2/√3`
* `minSideTri_three : minSideTri 3 = 3/2 + √3`
* `minSideTri_four  : minSideTri 4 = 3 + 2/√3`

Each is an upper bound (an explicit packing, checked exactly in `ℚ(√3)` by `inTriB`/`sepB`)
and a lower bound (`le_of_checks`: the weighted point certificate, checked by `check` on three
angle bins, with total weight `< n`).
-/

namespace SquarePacking.Tri

open SquarePacking

/-! ## n = 2 -/

def sq2 : Fin 2 → Sq := ![⟨q (1/2) (1/3), q (1/2) 0, q 1 0, q 0 0⟩, ⟨q (3/2) (1/3), q (1/2) 0, q 1 0, q 0 0⟩]

theorem minSideTri_two : minSideTri 2 = 2 + 2 / Real.sqrt 3 := by
  have hL : N2.L.val = 2 + 2 / Real.sqrt 3 := by
    rw [two_div_sqrt3]; simp [N2.L]
  rw [← hL]
  apply minSideTri_eq
  · exact packs_of_squares 2 N2.L sq2 (fun _ => 0) (fun i => by fin_cases i <;> exact rep0 _ _)
      (fun i => by fin_cases i <;> decide +kernel)
      (fun i j h => by fin_cases i <;> fin_cases j <;> first | decide +kernel | exact absurd h (by decide))
  · exact le_of_checks 2 N2.L N2.yTop N2.pts (yTop_val (by decide +kernel)) N2.weights
      (by decide +kernel) N2.tree0 N2.tree1 N2.tree2 N2.check0 N2.check1 N2.check2

/-! ## n = 3 (Friedman's pinwheel) -/

def sq3 : Fin 3 → Sq := ![⟨q (1/2) (1/3), q (1/2) 0, q 1 0, q 0 0⟩,
  ⟨q (5/4) (7/12), q (1/4) (1/4), q 0 (1/2), q (1/2) 0⟩,
  ⟨q (1/2) (7/12), q (3/4) (1/2), q (1/2) 0, q 0 (1/2)⟩]

noncomputable def ang3 : Fin 3 → ℝ := ![0, Real.pi / 6, Real.pi / 3]

theorem minSideTri_three : minSideTri 3 = 3 / 2 + Real.sqrt 3 := by
  have hL : N3.L.val = 3 / 2 + Real.sqrt 3 := by simp [N3.L]
  rw [← hL]
  apply minSideTri_eq
  · refine packs_of_squares 3 N3.L sq3 ang3 (fun i => ?_) (fun i => by fin_cases i <;> decide +kernel)
      (fun i j h => by fin_cases i <;> fin_cases j <;> first | decide +kernel | exact absurd h (by decide))
    fin_cases i
    · exact rep0 _ _
    · exact rep6 _ _
    · exact rep3 _ _
  · exact le_of_checks 3 N3.L N3.yTop N3.pts (yTop_val (by decide +kernel)) N3.weights
      (by decide +kernel) N3.tree0 N3.tree1 N3.tree2 N3.check0 N3.check1 N3.check2

/-! ## n = 4 -/

def sq4 : Fin 4 → Sq := ![⟨q (1/2) (1/3), q (1/2) 0, q 1 0, q 0 0⟩,
  ⟨q (3/2) (1/3), q (1/2) 0, q 1 0, q 0 0⟩, ⟨q (5/2) (1/3), q (1/2) 0, q 1 0, q 0 0⟩,
  ⟨q (3/2) (1/3), q (3/2) 0, q 1 0, q 0 0⟩]

theorem minSideTri_four : minSideTri 4 = 3 + 2 / Real.sqrt 3 := by
  have hL : N4.L.val = 3 + 2 / Real.sqrt 3 := by
    rw [two_div_sqrt3]; simp [N4.L]
  rw [← hL]
  apply minSideTri_eq
  · exact packs_of_squares 4 N4.L sq4 (fun _ => 0) (fun i => by fin_cases i <;> exact rep0 _ _)
      (fun i => by fin_cases i <;> decide +kernel)
      (fun i j h => by fin_cases i <;> fin_cases j <;> first | decide +kernel | exact absurd h (by decide))
  · exact le_of_checks 4 N4.L N4.yTop N4.pts (yTop_val (by decide +kernel)) N4.weights
      (by decide +kernel) N4.tree0 N4.tree1 N4.tree2 N4.check0 N4.check1 N4.check2

end SquarePacking.Tri
