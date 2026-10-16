import Lake
open Lake DSL
package sqpack where
  leanOptions := #[⟨`pp.unicode.fun, true⟩, ⟨`relaxedAutoImplicit, false⟩,
    ⟨`weak.linter.mathlibStandardSet, true⟩, ⟨`maxSynthPendingDepth, 3⟩]
require mathlib from git "https://github.com/leanprover-community/mathlib4" @ "v4.33.1"
lean_lib ClosedForm
@[default_target] lean_lib Sqpack
