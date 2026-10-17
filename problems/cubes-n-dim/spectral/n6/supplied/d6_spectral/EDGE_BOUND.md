# A missing-edge correction to the covariance bound

This proof works in any dimension n. Let U=[x C] be orthogonal, x>=0, p_i=x_i^2, and z_k=diag(x)C[:,k] for k=1,...,n-1. Define s_k=||z_k||_1 and t_k=||z_k||_2. Then each z_k has zero coordinate sum and ZZ^T=B=diag(p)-pp^T. Put L=sum s_k and T=Tr sqrt(B).

Let R_n(p) be the sum of the binomial(n,2)-(n-1) smallest numbers among {p_i p_j:i<j}. Then

    L >= sqrt(2) T + R_n(p)/2.

## Proof

For nonzero z_k, let A_k and B_k be its largest positive and largest negative absolute coordinate values. Its positive and negative sums each equal s_k/2, so

    t_k^2 <= (s_k/2)(A_k+B_k).

Keep only those two extreme coordinates to form d_k, and write r_k=z_k-d_k and rho_k=||r_k||_1. Thus

    rho_k=s_k-A_k-B_k <= s_k-2t_k^2/s_k.

Mark the unordered pair of kept coordinates as an edge. Ignore zero columns, which contribute nothing. The union E of marked edges has size at most n-1. For every pair i<j outside E, (d_k)_i(d_k)_j=0 for every k. Therefore

    sum_{(i,j) outside E} p_i p_j
      = sum_{(i,j) outside E} |B_ij|
      <= sum_k sum_{i<j} |(z_k)_i(z_k)_j-(d_k)_i(d_k)_j|
      <= sum_k [s_k^2-(s_k-rho_k)^2]/2
      <= sum_k s_k rho_k
      <= sum_k (s_k^2-2t_k^2).

The second inequality follows directly because d_k is a coordinate restriction of z_k: only products involving removed coordinates remain, and discarding the diagonal terms can only increase their sum. The left hand side is at least R_n(p), since at most n-1 pairs were deleted.

Zero sum implies s_k>=sqrt(2)t_k. Also weighted Cauchy-Schwarz gives s_k=sum_i x_i|C_ik|<=||x||_2||C[:,k]||_2=1. Consequently

    s_k^2-2t_k^2
      =(s_k-sqrt(2)t_k)(s_k+sqrt(2)t_k)
      <=2(s_k-sqrt(2)t_k).

Hence L>=sqrt(2)sum t_k+R_n(p)/2>=sqrt(2)T+R_n(p)/2, using the nuclear norm triangle inequality. QED.

## Six-dimensional corrected sufficient inequality

In n=6, R_6 is the sum of the ten smallest pair products, and

    1-F_j >= q(p)+R_6(p)/2.

At uniform p, the correction is 5/36. On p=(a,(1-a)/5,...), a>=1/6, the correction is (1-a)^2/5. Numerical multistart minimization suggests positivity on max p<=13/20; this is being subjected to an exact certificate, and is not proved by the numerical optimization alone.

## Rigorous simplex acceptance for the correction

For simplex vertices v^k and p=sum theta_k v^k, let Delta_i=max_k v_i^k-min_k v_i^k. For each pair, the bounded-variable covariance inequality gives

    p_i p_j >= sum_k theta_k v_i^k v_j^k - Delta_i Delta_j/4.

For any set H of ten pairs, summing, then minimizing over H, yields

    R_6(p) >= sum_k theta_k R_6(v^k) - sum_{i<j} Delta_i Delta_j/4.

This uses min_H sum_k theta_k A_k(H)>=sum_k theta_k min_H A_k(H). Therefore the original d5 simplex square-root chord loss, plus sum_{i<j}Delta_i Delta_j/8, bounds the interpolation loss of q+R_6/2. Every vertex value of R_6 is exact rational.

## Spectral-radius correction (additional rigorous strengthening)

Let lambda be any upper bound for the largest eigenvalue of B, and set delta_k=s_k-sqrt(2)t_k>=0 and D=sum delta_k. Since t_k<=sqrt(lambda),

    R_n <= sum(s_k^2-2t_k^2)
        =sum delta_k^2+2sqrt(2)sum t_k delta_k
        <=D^2+2sqrt(2lambda)D.

Solving this quadratic gives

    L >= sqrt(2)T+sqrt(2lambda+R_n)-sqrt(2lambda).

This bound is valid even without s_k<=1. At uniform p, use lambda=1/n. The resulting uniform-column lower bound is positive through n=10 (numerical evaluation; exact radical verification can be performed separately).

## Stronger quadratic missing-edge correction (rigorous)

Retain the largest positive/negative coordinates of each z. Write a=s/2, and let rp,rn be the sums of discarded positive and discarded negative absolute coordinates, rho=rp+rn, and v=the discarded squared Euclidean norm. The retained coordinates are a-rp and -(a-rn), so exactly

    d/2=(s^2-2t^2)/2=s*rho-(rp^2+rn^2+v).

The total absolute offdiagonal pair mass involving discarded coordinates is exactly

    E=s*rho-rho^2/2-v/2.

Consequently

    E-d/2=(rp-rn)^2/2+v/2 <=rho^2,

since v<=rp^2+rn^2. The missing edges in the previous proof contribute at most sum E, hence R_n<=sum(d/2+rho^2).

As previously, rho<=d/s<=2delta, where delta=s-sqrt(2)t>=0. With D=sum delta and t<=sqrt(lambda),

    R_n <= (1/2)sum delta^2 +sqrt(2)sum t*delta +4sum delta^2
        <= (9/2)D^2+sqrt(2lambda)D.

Therefore

    L >= sqrt(2)T + [sqrt(2lambda+18R_n)-sqrt(2lambda)]/9.

All zero-column terms are omitted, and the formulas extend by continuity. This is a valid strengthening; the best usable lower bound can take the maximum of this correction, the earlier spectral-radius correction, and R_n/2.

A global choice lambda=1/2 is valid for every probability vector: B is a weighted graph Laplacian, and the absolute sum of row i is 2p_i(1-p_i)<=1/2, so its spectral radius is at most1/2. Thus the especially simple bound is

    1-F_j >= q(p) + f(R_n(p)),
    f(R)=(sqrt(1+18R)-1)/9.

Here f is increasing and concave with derivative at most1. Since R_6(p)>=sum theta R_6(v)-E with E=sum_{i<j}Delta_i Delta_j/4, we have f(R_6(p))>=sum theta f(R_6(v))-E. This follows by concavity and the derivative bound; if the lower argument is negative, use f(R)>=0 and f(r)<=r. Thus exact simplex acceptance uses the old square-root chord loss plus sum Delta_i Delta_j/4. No variable spectral-radius certification is required for this global version.
