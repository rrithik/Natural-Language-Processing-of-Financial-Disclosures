import csv
from typing import List


def write_topics_to_csv(
    filename: str,
    topics: List[str],
    scores: List[float]
) -> None:
    """
    Writes topics and their scores to a CSV file.

    CSV format:
    topic,score

    :param filename: Output CSV filename
    :param topics: List of topic names
    :param scores: List of topic scores (same length as topics)
    """
    if len(topics) != len(scores):
        raise ValueError("topics and scores must be the same length")

    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["topic", "score"])

        for topic, score in zip(topics, scores):
            writer.writerow([topic, score])
