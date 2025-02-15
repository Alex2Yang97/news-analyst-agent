import pytest
from news_analyst_agent.agents.news_agent import NewsAnalystAgent
from langchain_core.messages import HumanMessage
from news_analyst_agent.agents.utils import ModelName

@pytest.mark.asyncio
async def test_news_analyst_invoke_tools():
    agent = NewsAnalystAgent(model_name=ModelName.LLAMA_3_2)
    msg_lst = [HumanMessage(content="summary tesla recent news")]
    results = await agent.arun(msg_lst)
    
    assert len(results["messages"]) > 0
    assert len(results["metadata"]["news"]) > 0


@pytest.mark.asyncio
async def test_news_analyst_agent_stream():
    agent = NewsAnalystAgent(model_name=ModelName.LLAMA_3_2)
    messages = [HumanMessage(content="summary tesla recent news")]
    
    news_received = False
    response_received = False
    
    async for chunk in agent.astream(messages):
        assert isinstance(chunk, dict)
        if "news" in chunk:
            news_received = True
            assert isinstance(chunk["news"], list)

        if "chunk" in chunk:
            response_received = True
            assert isinstance(chunk["chunk"], str)
    
    assert news_received, "Should have received news results"
    assert response_received, "Should have received AI response"
