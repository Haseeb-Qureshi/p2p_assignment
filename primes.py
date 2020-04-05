import gmpy2 as mp

def find_next_mersenne_prime(earlier_prime):
    p = earlier_prime + 1
    while not lucas_lehmer_test(p): p += 1
    return p

def lucas_lehmer_test(n):
    if n == 2: return True
    if not mp.is_prime(n): return False
    two = mp.mpz(2)
    m = two ** n - 1
    s = two * two

    for i in range(2, n):
        square = s * s
        s = (square & m) + (square >> n)
        if s >= m:
            s -= m
        s -= two

    return mp.is_zero(s)
