import json
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from itertools import chain
from typing import Annotated, List, Set
from uuid import uuid4

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.messages.base import BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from loguru import logger

from news_analyst_agent.agents.news_analyst_prompts import (
    ARG_ENTITIES_PROMPT,
    ARG_QUERY_PROMPT,
    NEWS_ANALYST_AGENT_SYSTEM_PROMPT,
)
from news_analyst_agent.agents.utils import (
    ModelName,
    NewsAnalystState,
    get_llm,
    retry_with_backoff,
)
from news_analyst_agent.tools.ddg_search import ddg_search
from news_analyst_agent.tools.yfinance_news import yf_tool


@tool
def news_retriever(
    query: Annotated[str, ARG_QUERY_PROMPT],
    entities: Annotated[list[str], ARG_ENTITIES_PROMPT],
):
    """Tool that retrieves news, articles, and research reports"""
    return

@tool
def chat_with_user(
    query: Annotated[str, "response for user"],
):
    """Tool for chatting with user. This tool cannot be used with other tools."""
    return query


class NewsAnalystAgent:
    def __init__(self, model_name: ModelName = ModelName.LLAMA_3_2, tracing: bool = False):
        logger.info("Initializing NewsAnalystAgent")
        if model_name == ModelName.LLAMA_3_2:
            self.tools = [news_retriever, chat_with_user]
        else:
            self.tools = [news_retriever]
        self.model = get_llm(model_name, self.tools)
        self.thread_id = str(uuid4())
        if tracing:
            self.config = {
                "configurable": {
                    "thread_id": self.thread_id
                }
            }
        else:
            self.config = None
        self.agent = self.create_agent()

    def invoke_tools(self, query: str, entities: list[str]) -> List[dict]:
        """Execute multiple news retrieval tools in parallel"""
        logger.debug(f"Invoking news retrieval tools with query: {query}")
        tasks = [
            (partial(retry_with_backoff, ddg_search.invoke), query),
        ]
        if entities:
            for entity in entities:
                tasks.append(
                    (partial(retry_with_backoff, yf_tool.invoke), entity)
                )

        remove_duplicates: Set[str] = set()
        filtered_res_lst = []
        
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(func, *args) for func, *args in tasks]
            res_lst = [future.result() for future in futures]
            res_lst = list(chain.from_iterable(res_lst))

        for r in res_lst:
            if r and r["link"] not in remove_duplicates:
                remove_duplicates.add(r["link"])
                filtered_res_lst.append(r)
        
        logger.debug(f"Retrieved {len(filtered_res_lst)} unique news items")
        return filtered_res_lst

    def node_call_tools(self, state: NewsAnalystState) -> dict:
        """Handle tool calls and retrieve news"""
        tool_call = state["messages"][-1].tool_calls[0]
        query = tool_call["args"]["query"]
        entities = tool_call["args"]["entities"]
        logger.info(f"Processing tool call with query: {query}")

        response = self.invoke_tools(query, entities)
        logger.info(f"News retriever found {len(response)} articles")
        
        content = json.dumps([
            {
                "title": item["title"],
                "description": item["description"]
            } for item in response
        ])
        
        message = ToolMessage(
            content=content,
            name="news_retriever",
            tool_call_id=tool_call["id"],
        )
        
        logger.debug("News retriever message created successfully")
        return {
            "messages": [message],
            "metadata": {
                "news": response
            }
        }
        
    def node_chat_with_user(self, state: NewsAnalystState) -> dict:
        """Tool for chatting with user. Only for llama3.2"""
        tool_call = state["messages"][-1].tool_calls
        for tool in tool_call:
            if tool["name"] == "chat_with_user":
                assistant_response = tool["args"]["query"]
        
        state["messages"].pop(-1)
        ai_message = AIMessage(content=assistant_response)
        return {
            "messages": [ai_message],
            "metadata": {}
        }

    def call_model(self, state: NewsAnalystState, config: RunnableConfig) -> dict:
        """Call the LLM with the current state"""
        logger.debug("Calling LLM model")
        system_prompt = SystemMessage(NEWS_ANALYST_AGENT_SYSTEM_PROMPT)
        response = self.model.invoke([system_prompt] + state["messages"], config)
        logger.debug("LLM response received")
        return {"messages": [response]}

    @staticmethod
    def should_continue(state: NewsAnalystState) -> List[str]:
        """Determine if the agent should continue processing"""
        messages = state["messages"]
        last_message = messages[-1]
        if not last_message.tool_calls:
            logger.debug("No more tool calls, ending processing")
            return [END]

        for tool in last_message.tool_calls:
            if tool["name"] == "chat_with_user":
                return ["chat_with_user"]

        logger.debug("Continuing with news retriever")
        return ["news_retriever"]

    def create_agent(self):
        """Create and configure the agent workflow"""
        logger.info("Creating news analyst agent workflow")
        workflow = StateGraph(NewsAnalystState)

        workflow.add_node("agent", self.call_model)
        workflow.add_node("news_retriever", self.node_call_tools)
        workflow.add_node("chat_with_user", self.node_chat_with_user)

        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            ["chat_with_user", "news_retriever", END]
        )
        workflow.add_edge("news_retriever", "agent")
        workflow.add_edge("chat_with_user", END)

        logger.info("News analyst agent workflow created successfully")
        return workflow.compile()
    
    async def arun(self, msg_lst: list[BaseMessage]):
        """Run the news analyst agent asynchronously"""
        res = await self.agent.ainvoke(
            input={
                "messages": msg_lst,
                "metadata": {}
            },
            config=self.config
        )
        return res
    
    async def astream(self, msg_lst: list[BaseMessage], json_mode: bool = False):
        """Stream the news analyst agent"""
        async for streaming_msg, _ in self.agent.astream(
            {"messages": msg_lst, "metadata": {}}, stream_mode="messages",
            config=self.config
        ):
            if not json_mode:
                if streaming_msg.content:
                    if isinstance(streaming_msg, ToolMessage):
                        yield {"news": eval(streaming_msg.content)}
                    if isinstance(streaming_msg, AIMessage):
                        yield {"chunk": streaming_msg.content}
            elif streaming_msg.content:
                if isinstance(streaming_msg, ToolMessage):
                    yield json.dumps({"news": eval(streaming_msg.content)})
                if isinstance(streaming_msg, AIMessage):
                    yield json.dumps({"chunk": streaming_msg.content})
    
