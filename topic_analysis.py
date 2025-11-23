import re
from collections import Counter

# ---- Step 1: Read local text file ----
file_path = "Disney.txt"  # replace with your file name
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read().lower()

# ---- Step 2: Clean text ----
text = re.sub(r"[^a-z\s]", "", text)  # remove punctuation, numbers, etc.
words = text.split()

# ---- Step 3: Define common stopwords ----
stopwords = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "then",
    "because",
    "as",
    "in",
    "on",
    "at",
    "by",
    "for",
    "of",
    "to",
    "from",
    "with",
    "about",
    "over",
    "under",
    "between",
    "through",
    "during",
    "before",
    "after",
    "is",
    "am",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "shall",
    "should",
    "may",
    "might",
    "must",
    "can",
    "could",
    "he",
    "she",
    "it",
    "they",
    "them",
    "we",
    "us",
    "you",
    "i",
    "me",
    "my",
    "your",
    "his",
    "her",
    "their",
    "our",
    "this",
    "that",
    "these",
    "those",
    "not",
    "no",
    "yes",
    "just",
    "too",
    "also",
    "very",
}

# ---- Step 4: Filter out stopwords ----
cleaned_words = [word for word in words if word not in stopwords and len(word) > 2]

# ---- Step 5: Count word frequencies ----
total_words = len(cleaned_words)
word_counts = Counter(cleaned_words)
common_words = word_counts.most_common(15)

# ---- Step 6: Print top words with percentages ----
print("Top 15 most common words in this filing:\n")
for word, count in common_words:
    percent = (count / total_words) * 100
    print(f"{word:<15} {count:>5} times   ({percent:.2f}% of total words)")

# ---- Step 7: Basic topic grouping (simple keyword-based) ----
topic_keywords = {
    "Financial Performance": {
        "revenue",
        "profit",
        "loss",
        "earnings",
        "income",
        "sales",
        "growth",
    },
    "Management/Leadership": {
        "board",
        "executive",
        "director",
        "ceo",
        "management",
        "leadership",
    },
    "Risk/Compliance": {
        "risk",
        "liability",
        "regulation",
        "uncertainty",
        "lawsuit",
        "exposure",
    },
    "Market/Operations": {
        "market",
        "product",
        "operations",
        "strategy",
        "customer",
        "investment",
    },
}

print("\nEstimated topic distribution:\n")
for topic, keywords in topic_keywords.items():
    topic_count = sum(word_counts[word] for word in keywords if word in word_counts)
    percent = (topic_count / total_words) * 100
    print(f"{topic:<25}: {topic_count:>5} words  ({percent:.2f}% of total)")
