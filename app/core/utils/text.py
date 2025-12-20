"""
Text

هذا الملف جزء من مشروع CogniForge.
"""

from collections import Counter


def get_ngrams(tokens: list[str], n: int) -> Counter:
    """Get n-grams from tokens"""
    ngrams = []
    for i in range(len(tokens) - n + 1):
        ngrams.append(tuple(tokens[i : i + n]))
    return Counter(ngrams)


def get_lcs_length(seq1: list, seq2: list) -> int:
    """Calculate longest common subsequence length"""
    m, n = len(seq1), len(seq2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]
