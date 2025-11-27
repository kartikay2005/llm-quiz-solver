"""Unit tests for quiz solver components."""
import pytest
from app.quiz.extractor import parse_html_for_quiz, parse_llm_response
from app.quiz.llm import parse_llm_response


def test_parse_html_for_quiz():
    """Test HTML parsing extracts question."""
    html = """
    <html>
        <body>
            <h1 class="question">What is 2+2?</h1>
            <form action="/submit">
                <input type="submit">
            </form>
        </body>
    </html>
    """
    result = parse_html_for_quiz(html)
    assert "2+2" in result["question"]
    assert result["submit_url"] == "/submit"


def test_parse_llm_response_json():
    """Test parsing JSON response."""
    response = '{"answer": 42}'
    parsed = parse_llm_response(response)
    assert isinstance(parsed, dict)
    assert parsed["answer"] == 42


def test_parse_llm_response_number():
    """Test parsing numeric response."""
    assert parse_llm_response("42") == 42
    assert parse_llm_response("3.14") == 3.14


def test_parse_llm_response_boolean():
    """Test parsing boolean response."""
    assert parse_llm_response("true") is True
    assert parse_llm_response("false") is False


def test_parse_llm_response_string():
    """Test parsing string response."""
    result = parse_llm_response("hello world")
    assert result == "hello world"
