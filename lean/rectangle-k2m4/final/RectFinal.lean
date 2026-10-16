import Sqpack.V9.Main
import Sqpack.Rect4

/-! Theorem 1 of `problems/rectangle-upper-bounds/` without hypotheses: the conditional theorem
`Rect4.rect4_of_validTilt9` applied to the kernel proof `LemmaELeaf.validTilt9` of `Bentz4.ValidTilt9`
(release `validtilt9-lean-v1`). Both refer to the same constant `SquarePacking.Bentz4.ValidTilt9`, defined in the
same file `Sqpack/ValidSplit9.lean` (byte-identical in both projects). -/

namespace SquarePacking
namespace Rect4

theorem rect4 :
    ∀ A B : ℕ, 8 ≤ A → 8 ≤ B → ∀ a b : ℝ, a < A → b < B →
      ¬ UnitSquarePacking.Conjectures.PacksRect (A * B - 4) a b :=
  rect4_of_validTilt9 LemmaELeaf.validTilt9

end Rect4
end SquarePacking
