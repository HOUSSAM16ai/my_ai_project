
def solve_math():
    print("Solving Math Problems...")

    # Problem 1
    # A = [-3, 5]
    # B = (-inf, 2)

    # A intersection B: overlap of [-3, 5] and (-inf, 2)
    # intersection is [-3, 2)
    # Arabic: [-3, 2[

    # A union B: combine [-3, 5] and (-inf, 2)
    # union is (-inf, 5]
    # Arabic: ]-inf, 5]

    # A - B: elements in A not in B
    # A = [-3, 5], B = (-inf, 2)
    # Remaining: [2, 5]
    # Arabic: [2, 5]

    # B - A: elements in B not in A
    # B = (-inf, 2), A = [-3, 5]
    # Remaining: (-inf, -3)
    # Arabic: ]-inf, -3[

    print("Problem 1 (Sets A & B):")
    print(f"A = [-3, 5], B = ]-inf, 2[")
    print(f"A ∩ B = [-3, 2[")
    print(f"A U B = ]-inf, 5]")
    print(f"A - B = [2, 5]")
    print(f"B - A = ]-inf, -3[")
    print("-" * 20)

    # Problem 2
    # X = (-inf, 3]
    # Y = (-2, 7)

    # X intersection Y: overlap of (-inf, 3] and (-2, 7)
    # intersection is (-2, 3]
    # Arabic: ]-2, 3]

    # X union Y: combine (-inf, 3] and (-2, 7)
    # union is (-inf, 7)
    # Arabic: ]-inf, 7[

    print("Problem 2 (Sets X & Y):")
    print(f"X = ]-inf, 3], Y = ]-2, 7[")
    print(f"X ∩ Y = ]-2, 3]")
    print(f"X U Y = ]-inf, 7[")
    print("-" * 20)

    # Problem 3
    # |2x - 3| <= 7
    # -7 <= 2x - 3 <= 7
    # -4 <= 2x <= 10
    # -2 <= x <= 5
    # Solution set: [-2, 5]

    print("Problem 3 (Inequality):")
    print("|2x - 3| <= 7")
    print("-7 <= 2x - 3 <= 7")
    print("-4 <= 2x <= 10")
    print("-2 <= x <= 5")
    print("S = [-2, 5]")

if __name__ == "__main__":
    solve_math()
