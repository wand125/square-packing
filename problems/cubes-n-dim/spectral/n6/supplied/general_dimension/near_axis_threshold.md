# Exact improved threshold for the quadratic minorant implication

Suppose the full minorant C_m has been proved. For target column x=(a,b,0,...) with a>=0, s=||b||, and a²+s²=1, covariance summation gives

Phi/2-(a+sum b-1) >= 1-a-s³ = s²[1/(1+a)-s].

Therefore it suffices that s(1+a)<=1. Squaring nonnegative quantities, this is equivalent to

g(a)=(1-a)(1+a)^3<=1.

For a>=1/2, g'(a)=2(1+a)^2(1-2a)<=0. At the exact rational point a=21/25,

g(21/25)=389344/390625<1.

Consequently every a²>=441/625=0.7056 is covered. In particular a²>=71/100 is covered because 71/100>441/625.

This replaces the earlier convenient threshold 3/4 wherever the C_m near-axis implication is used. It is unconditional for m<=5, whose minorants have now been independently audited. See rank_five_minorant_audit.md for the independent C5 and threshold verification.

For sharper rational endpoints, a=8393/10000 also works by direct integer arithmetic, giving a²>=70442449/100000000=0.70442449. The simpler 441/625 threshold is generally preferable unless the additional narrow interval matters.

## Equivalent polynomial condition in p

For a>0, expand g(a)<=1 and divide by a to obtain a³+2a²>=2. With p=a² in [0,1], both sides in p sqrt(p)>=2(1-p) are nonnegative, so this is exactly equivalent to

p³-4(1-p)²>=0.

This polynomial is strictly increasing on [0,1], since its derivative is 3p²+8(1-p)>0. At p=71/100 its exact value is 21511/1000000>0. At p=141/200=.705 its exact value is 18421/8000000>0. Thus the simpler p>=.705 threshold also works. At p=70441/100000=.70441 the value is 29834376121/10^15>0, if a still sharper rational endpoint is wanted. No numerical root approximation is needed.
