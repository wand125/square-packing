import Mathlib.Data.List.GetD
import Mathlib.Data.List.Perm.Basic
import Mathlib.Data.List.Range

namespace ClosedForm

/-- Both recursive arguments have explicit fuel so kernel reduction does not
need to unfold well-founded recursion proofs. At exhausted fuel, concatenation
still preserves all entries. -/
def mergeIndices : ℕ → List ℕ → List ℕ → List ℕ
  | 0, xs, ys => xs ++ ys
  | _+1, [], ys => ys
  | _+1, xs, [] => xs
  | n+1, x::xs, y::ys =>
    if x ≤ y then x :: mergeIndices n xs (y::ys)
    else y :: mergeIndices n (x::xs) ys

lemma mergeIndices_perm (n : ℕ) (xs ys : List ℕ) :
    (mergeIndices n xs ys).Perm (xs ++ ys) := by
  induction n generalizing xs ys with
  | zero => exact List.Perm.refl _
  | succ n ih =>
    cases xs with
    | nil => simp [mergeIndices]
    | cons x xs =>
      cases ys with
      | nil => simp [mergeIndices]
      | cons y ys =>
        simp only [mergeIndices]
        split
        · exact (ih xs (y::ys)).cons x
        · exact ((ih (x::xs) ys).cons y).trans List.perm_middle.symm

/-- Any fuel preserves the multiset; a checked equality certifies enough fuel. -/
def sortIndices : ℕ → List ℕ → List ℕ
  | 0, xs => xs
  | n+1, xs =>
    mergeIndices xs.length (sortIndices n (xs.take (xs.length/2)))
      (sortIndices n (xs.drop (xs.length/2)))

lemma sortIndices_perm (n : ℕ) (xs : List ℕ) : (sortIndices n xs).Perm xs := by
  induction n generalizing xs with
  | zero => exact List.Perm.refl _
  | succ n ih =>
    dsimp only [sortIndices]
    have h := (mergeIndices_perm xs.length _ _).trans
      ((ih (xs.take (xs.length/2))).append (ih (xs.drop (xs.length/2))))
    simpa only [List.take_append_drop] using h

example : sortIndices 2 [3,1,2] = [1,2,3] := by decide +kernel

lemma map_range_getD {α : Type*} (xs : List α) (d : α) :
    (List.range xs.length).map (fun i => xs.getD i d) = xs := by
  apply List.ext_getElem
  · simp
  · intro i h1 h2
    simp [h2]

/-- Only small indices are compared by the permutation decision. The separate
integer row-link equality checks every selected value, not a digest. -/
lemma perm_of_indices {α : Type*} (xs ys : List α) (d : α) (is : List ℕ)
    (hp : (List.range xs.length).Perm is)
    (he : is.map (fun i => xs.getD i d) = ys) : xs.Perm ys := by
  have h := hp.map (fun i => xs.getD i d)
  rwa [map_range_getD, he] at h

#print axioms perm_of_indices
end ClosedForm
