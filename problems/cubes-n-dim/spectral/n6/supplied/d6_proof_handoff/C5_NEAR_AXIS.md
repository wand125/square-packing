# Stronger near-axis theorem from the audited C5 minorant

Status: the C5 minorant and this near-axis consequence are proved and independently audited. This section does not by itself certify the remaining far region or assert the complete six-dimensional theorem.

## The minorant

For b in R^5 with b_i>=0, define the symmetric matrix H(b) by

    H_ii=b_i,
    2H_ij=b_i+b_j-sqrt(b_i^2+b_j^2)  (i!=j).

The audited C5 theorem states that, for every v in R^5 with ||v||_2<=1,

    v^T H(b)v <= f_b(v):=(|b dot v|+sum_i b_i|v_i|)/2.       (C5)

The positive-vector allocation proof, exact saved-tree certificate, standalone rational replay, and sign-lifting audit are supplied in `../general_dimension/positive_c5_certificate_proof.md`, `../general_dimension/positive_c5_exact_tree.json.gz`, `../general_dimension/replay_positive_c5_exact_tree.py`, and `../general_dimension/rank_five_minorant_audit.md`. The exact replay checks 15,785 records, 7,893 leaves, maximum depth 24, and covered relative volume 1.

## Covariance summation

Let x be a nonnegative unit target column, supported on at most six coordinates, in an orthogonal matrix of ambient dimension at least six. Smaller ambient dimensions are first embedded by adjoining an identity block, which leaves F for every original column unchanged. Choose its largest coordinate a and write its remaining nonzero coordinates, padded with zeros, as b in R^5. Put s=||b||_2, so a^2+s^2=1. For a completion column y, let v be the restriction to these five tail rows. Then ||v||_2<=1, and orthogonality gives

    a y_1=-b dot v.

Its weighted l1 contribution is therefore

    a|y_1|+sum_i b_i|v_i|=2f_b(v)>=2v^T H(b)v.

If v_k are these restrictions for all completion columns, row orthogonality gives

    sum_k v_k v_k^T=I_5-bb^T.

Consequently the total weighted completion cost L satisfies

    L/2 >= Tr(H(b)(I_5-bb^T))
         =sum_i b_i-b^T H(b)b.

If s=0, the target is a coordinate vector and F=1 immediately. Otherwise apply C5 at the nonnegative unit vector b/s. Here f_b(b/s)=s, hence

    b^T H(b)b<=s^3.

Writing S=a+sum_i b_i and F=2S-1-L gives

    1-F >=2(1-a-s^3)
         =2s^2[1/(1+a)-s].                                (1)

No row-l1 hypothesis and no frame-compression argument is used.

## Exact threshold

The bracket in (1) is nonnegative precisely when

    (1-a)(1+a)^3<=1.

For a>0, expand and divide by a to obtain a^3+2a^2>=2. Set p=a^2. Since both sides of p^(3/2)>=2(1-p) are nonnegative, the condition is equivalent to

    g(p):=p^3-4(1-p)^2>=0.

On [0,1], g'(p)=3p^2+8(1-p)>0, and the exact endpoint calculation is

    g(141/200)=18421/8000000>0.

Thus every target supported on at most six coordinates satisfies F<=1 in every ambient dimension whenever its maximum squared coordinate is at least 141/200. The inequality is strict except at a coordinate target.

## How this can strengthen the dimension-six conclusion

For an actual six-by-six orthogonal matrix, all columns are supported on at most six coordinates. The audited cap certificate already handles max p<=13/20 without a row-feasibility assumption. The fully verified long strip covers this interval, so together these results establish unrestricted F6 for every matrix in O(6).

The strip to 159/200 passed both exact replays. Its overlap with this near-axis region creates no gap. A six-dimensional far-region certificate cannot automatically be extended to arbitrary ambient dimension, because its missing-edge bounds use exactly five completion columns.
