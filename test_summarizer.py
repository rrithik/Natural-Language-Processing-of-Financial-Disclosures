import os
import tempfile

from summarize_disclosure import summarize_disclosure


def test_summarize_disclosure_returns_string(monkeypatch):
    """
    Test that summarize_disclosure() returns a string when given a valid file and prompt.
    """

    # --- create a temporary text file ---
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        tmp.write("This is a sample financial disclosure for testing.")
        tmp_path = tmp.name

    # --- mock the Gemini API call (so test runs offline) ---
    def mock_genai_response(file_path, prompt):
        return "Mock summary result."

    # Replace the real function logic temporarily if it calls the API
    monkeypatch.setattr(
        "summarize_disclosure.summarize_disclosure", mock_genai_response
    )

    # --- run the test ---
    result = summarize_disclosure(tmp_path, "Summarize this document")
    assert isinstance(result, str)
    assert "summary" in result.lower()

    # cleanup
    os.remove(tmp_path)
