from typing import Iterable, List, Literal, Optional, Type

from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.documents import Document
from langchain_core.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field


class DDGInput(BaseModel):
    """Input for the DuckDuckGo search tool."""

    query: str = Field(description="search query to look up")


class DuckDuckGoSearchResults(BaseTool):  # type: ignore[override, override]
    """Tool that queries the DuckDuckGo search API and
    returns the results in `output_format`.
    """

    name: str = "duckduckgo_results_json"
    description: str = (
        "A wrapper around Duck Duck Go Search. "
        "Useful for when you need to answer questions about current events. "
        "Input should be a search query."
    )
    max_results: int = Field(alias="num_results", default=5)
    api_wrapper: DuckDuckGoSearchAPIWrapper = Field(
        default_factory=DuckDuckGoSearchAPIWrapper
    )
    backend: str = "text"
    args_schema: Type[BaseModel] = DDGInput
    keys_to_include: Optional[List[str]] = None
    """Which keys from each result to include. If None all keys are included."""
    results_separator: str = ", "
    """Character for separating results."""

    response_format: Literal["content"] = "content"

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> list[dict]:
        """Use the tool."""
        logger.debug(f"Use ddg_search tool with query: {query}")
        try:
            raw_results = self.api_wrapper.results(
                query, self.max_results, source=self.backend
            )
        except Exception as e:
            logger.exception(f"ddg_search: Search error {e}")
            raise
        
        if not raw_results:
            logger.warning(f"ddg_search: No news found for {query}.")
            return []

        filtered_results = [
            {
                k: v
                for k, v in d.items()
                if not self.keys_to_include or k in self.keys_to_include
            }
            for d in raw_results
        ]
        
        # links = [d["link"] for d in filtered_results]
        # loader = WebBaseLoader(web_paths=links)
        # docs = loader.load()
        # formatted_results = self._format_results(docs)
        
        formatted_results = [{
            "title": d["title"],
            "description": d["snippet"],
            "content": None,
            "link": d["link"],
            "query": query,
            "source": "ddg",
        } for d in filtered_results]
        return formatted_results

    @staticmethod
    def _format_results(docs: Iterable[Document], query: str) -> list[dict]:
        formatted_docs = []
        for doc in docs:
            formatted_docs.append({ 
                "title": doc.metadata["title"],
                "description": doc.metadata["description"],
                "content": doc.page_content,
                "link": doc.metadata["source"],
                "query": query,
                "source": "ddg",
            })
        return formatted_docs

wrapper = DuckDuckGoSearchAPIWrapper()
ddg_search = DuckDuckGoSearchResults(api_wrapper=wrapper, backend="news")
