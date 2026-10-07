import Sqtri.Upper
import Sqtri.Data.M9.All

/-! A lower bound only: 37 unit squares do not fit in an equilateral triangle of side less than
`9 + 2/√3`.  (The rows construction holds only 36 squares at this side.) -/

namespace SquarePacking.Tri

theorem le_of_packs_37 : ∀ s, PacksTri 37 s → 9 + 2 / Real.sqrt 3 ≤ s := by
  have hL : M9.L.val = 9 + 2 / Real.sqrt 3 := by
    rw [two_div_sqrt3]; simp [M9.L]
  rw [← hL]
  exact le_of_checks 37 M9.L M9.yTop M9.pts (yTop_val (by decide +kernel)) M9.weights
    (by decide +kernel) M9.tree0 M9.tree1 M9.tree2 M9.check0 M9.check1 M9.check2

end SquarePacking.Tri
