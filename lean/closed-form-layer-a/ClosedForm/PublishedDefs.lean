import ClosedForm.Data.Families
import ClosedForm.Data.Intervals

namespace ClosedForm

/-- JSON's left endpoint flag is honored; all right endpoints are closed. -/
def I (i : Fin 34) : Set ℝ :=
  let v := Data.intervals i
  if v.openLeft then Set.Ioc (v.d0 : ℝ) (v.d1 : ℝ)
  else Set.Icc (v.d0 : ℝ) (v.d1 : ℝ)

noncomputable def certifiedLine (i : Fin 34) (δ : ℝ) : ℝ :=
  (Data.intervals i).alpha * δ + (Data.intervals i).beta

end ClosedForm
