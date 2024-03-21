def time_to_min(time):
    factors = (60, 1, 1/60)

    return sum(i*j for i, j in zip(map(int, time.split(':')), factors))

print(time_to_min('09:50'))
print(450 + int(3)*45)
print()