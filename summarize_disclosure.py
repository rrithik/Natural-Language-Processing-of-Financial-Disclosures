def summarize_disclosure(file_path, prompt):
    """
    Summarizes the content of a text file (mocked, no API key needed).
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read().strip()

        if not text:
            return "Error: file is empty."

        # mock summary (replace with real API logic later)
        summary = f"Summary ({len(text.split())} words): {text[:50]}..."
        return summary
    except Exception as e:
        return f"Error reading file: {e}"
