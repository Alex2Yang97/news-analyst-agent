# At the top of app.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from typing import cast

import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

from typing import Literal, Dict
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langchain.schema.runnable.config import RunnableConfig
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

import chainlit as cl
from chainlit.types import ThreadDict
from chainlit.types import (
    Feedback,
    PageInfo,
    PaginatedResponse,
    Pagination,
    ThreadDict,
    ThreadFilter,
)

from news_analyst_agent.agents.utils import get_llm, ModelName
from news_analyst_agent.agents.news_agent import NewsAnalystAgent

from news_analyst_agent.db.models import Thread, Step
from news_analyst_agent.db.database import AsyncSessionLocal

from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import MessagesState

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert

import uuid

SQLALCHEMY_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")

@cl.data_layer
def get_data_layer():
    return SQLAlchemyDataLayer(conninfo=SQLALCHEMY_DATABASE_URL, storage_provider=None)


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    correct_username = os.getenv("ADMIN_USERNAME", "admin")
    correct_password = os.getenv("ADMIN_PASSWORD", "admin")
    
    if (username, password) == (correct_username, correct_password):
        return cl.User(
            identifier=username,
            metadata={"role": "admin", "provider": "credentials"}
        )
    return None


@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="llama3.2:latest",
            markdown_description="The underlying LLM model is **LLAMA-3.2**.",
            icon="https://picsum.photos/200",
        ),
        cl.ChatProfile(
            name="gpt-4o",
            markdown_description="The underlying LLM model is **GPT-4**.",
            icon="https://picsum.photos/250",
        ),
        cl.ChatProfile(
            name="gpt-4o-mini",
            markdown_description="The underlying LLM model is **GPT-4o-mini**.",
            icon="https://picsum.photos/300",
        ),
    ]


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Tech Stock Impact Analysis",
            message="How will Microsoft's latest AI advancement affect other tech stocks in the market?",
            icon="/public/idea.svg",
        ),

        cl.Starter(
            label="AI Industry News",
            message="What's the impact of DeepSeek's latest AI model on Nvidia's market position and stock outlook?",
            icon="/public/idea.svg",
        ),
        cl.Starter(
            label="EV Market Analysis",
            message="How does Tesla's new investment in Mexico manufacturing affect their competitive position against BYD?",
            icon="/public/idea.svg",
        ),

        cl.Starter(
            label="Semiconductor Industry",
            message="What are the implications of TSMC's new chip factory announcement on AMD and Nvidia stock performance?",
            icon="/public/idea.svg",
        ),

        cl.Starter(
            label="Tech Layoff Impact",
            message="How are the recent tech layoffs at Google affecting the broader tech industry and market sentiment?",
            icon="/public/idea.svg",
        ),
    ]


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    pass


@cl.on_chat_start
async def on_chat_start():
    # Ensure Thread exists
    # This is a workaround for the fact that sometimes the thread is not created. Should be a bug in chainlit.
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        thread = await session.get(Thread, cl.context.session.thread_id)
        if not thread:
            thread = Thread(id=cl.context.session.thread_id, createdAt=datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
            session.add(thread)
            await session.commit()
            
    chat_profile = cl.user_session.get("chat_profile")
    cl.user_session.set("chat_profile", chat_profile)


async def get_thread_steps(thread_id: str):
    """
    Retrieve steps for a given thread from the database.
    
    Args:
        thread_id: The UUID of the thread
        
    Returns:
        List of Step objects for the thread
    """
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get the thread and its steps
        thread = await session.get(Thread, thread_id)
        if thread:
            return thread.steps
        return []


@cl.on_message
async def on_message(message: cl.Message):
    """
    This function is called every time a user inputs a message in the UI.
    It sends back an intermediate response from the tool, followed by the final answer.

    Args:
        message: The user's message.

    Returns:
        None.
    """

    input_lst = [HumanMessage(content=message.content)]

    chat_profile = cl.user_session.get("chat_profile")
    news_agent = NewsAnalystAgent(model_name=chat_profile)
    agent = news_agent.create_agent()
    use_tool = False
    
    async with cl.Step(name="Using tools") as step:
        step.input = "Using tools"
        step.output = ""
        
    ui_msg = cl.Message(content="")
    
    async for streaming_msg, _ in agent.astream(
        {"messages": input_lst, "metadata": {}}, stream_mode="messages",
    ):
        
        if isinstance(streaming_msg, ToolMessage):
            news_reference = eval(streaming_msg.content)
            step.input = "Retrieving news"
            step.output = news_reference
            await step.update()
            use_tool = True

        if isinstance(streaming_msg, AIMessage):
            await ui_msg.stream_token(streaming_msg.content)
        
        await ui_msg.update()

    if not use_tool:
        await step.remove()
