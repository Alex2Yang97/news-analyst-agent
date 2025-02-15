from typing import Iterable, Optional, Type
from loguru import logger

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.documents import Document
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from requests.exceptions import HTTPError, ReadTimeout
from urllib3.exceptions import ConnectionError

from langchain_community.document_loaders.web_base import WebBaseLoader


class YahooFinanceNewsInput(BaseModel):
    """Input for the YahooFinanceNews tool."""

    entity: str = Field(description="company ticker symbol or company name to look up")


class YahooFinanceNewsTool(BaseTool):  # type: ignore[override, override]
    """Tool that searches financial news on Yahoo Finance."""

    name: str = "yahoo_finance_news"
    description: str = (
        "Useful for when you need to find financial news "
        "about a public company. "
        "Input should be a company ticker or company name. "
        "For example, AAPL for Apple, MSFT for Microsoft, or openai."
    )
    top_k: int = 5
    """The number of results to return."""

    args_schema: Type[BaseModel] = YahooFinanceNewsInput

    def _run(
        self,
        entity: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> list[dict]:
        """Use the Yahoo Finance News tool."""
        entity = entity.lower()
        logger.debug(f"Use yfinance_news tool with query: {entity}")
        try:
            import yfinance
        except ImportError:
            raise ImportError(
                "Could not import yfinance python package. "
                "Please install it with `pip install yfinance`."
            )

        retrieved_news = yfinance.Search(entity, news_count=self.top_k).news
        links = []
        try:
            links = [n["link"] for n in retrieved_news if n["type"] == "STORY"]
        except (HTTPError, ReadTimeout, ConnectionError):
            logger.exception(f"yfinance_news: Network error {e}")
            raise
        except Exception as e:
            logger.exception(f"yfinance_news: Retrieve Error {e}")
            raise

        if not links:
            logger.warning(f"yfinance_news: No news found for {entity}.")
            return []
        
        loader = WebBaseLoader(web_paths=links)
        docs = loader.load()

        result = self._format_results(docs, entity)
        if not result:
            logger.warning(f"yfinance_news: No news found for {entity}.")
            return []
        return result

    @staticmethod
    def _format_results(docs: Iterable[Document], entity: str) -> list[dict]:
        formatted_docs = []
        for doc in docs:
            if entity in doc.metadata["description"].lower() or entity in doc.metadata["title"].lower():
                formatted_docs.append({ 
                    "title": doc.metadata["title"],
                    "description": doc.metadata["description"],
                    "content": doc.page_content,
                    "link": doc.metadata["source"],
                    "query": entity,
                    "source": "yfinance",
                })
        return formatted_docs

yf_tool = YahooFinanceNewsTool()
