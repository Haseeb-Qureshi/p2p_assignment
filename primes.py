from sympy import isprime

def find_next_mersenne_prime(earlier_prime):
    p = earlier_prime + 1
    while not lucas_lehmer_test(p): p += 1
    return p

def lucas_lehmer_test(n):
    if n == 2: return True
    if not isprime(n): return False
    m = 2 ** n - 1
    s = 4
    for i in range(2, n):
        square = s * s
        s = (square & m) + (square >> n)
        if s >= m:
            s -= m
        s -= 2
    return s == 0
