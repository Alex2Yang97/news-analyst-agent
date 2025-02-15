import pytest
from news_analyst_agent.tools.ddg_search import ddg_search
from news_analyst_agent.tools.yfinance_news import yf_tool


def test_ddg_search_tool():
    results = ddg_search.invoke("deepseek") 
    
    assert len(results) > 0
    for result in results:
        assert "title" in result
        assert "description" in result
        assert "content" in result
        assert "link" in result
        assert result["source"] == "ddg"


def test_yfinance_tool():
    results = yf_tool.invoke("AAPL")
    
    assert len(results) > 0
    for result in results:
        assert "title" in result
        assert "description" in result
        assert "content" in result
        assert "link" in result
        assert result["source"] == "yfinance"
