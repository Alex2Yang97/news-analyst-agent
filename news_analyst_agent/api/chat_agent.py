
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from loguru import logger
from pydantic import BaseModel

from news_analyst_agent.agents.news_agent import NewsAnalystAgent
from news_analyst_agent.agents.utils import ModelName
from news_analyst_agent.api.auth import verify_admin

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    model: ModelName = ModelName.LLAMA_3_2
    stream: bool = False
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Hello, how are you?"
                        },
                        {
                            "role": "assistant",
                            "content": "I'm fine, thank you!"
                        },
                        {
                            "role": "user",
                            "content": "how's tesla recent performance?"
                        }
                    ]
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    messages: list[Message]
    news: list[dict] | None = None


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    _: str = Depends(verify_admin)
):
    """Chat endpoint that uses NewsAnalystAgent"""
    try:
        model_name = request.model
        agent = NewsAnalystAgent(model_name=model_name)
        print(f"alex-debug request {request}")
        
        lg_msg_lst = []
        for msg in request.messages:
            if msg.role == "user":
                lg_msg_lst.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lg_msg_lst.append(AIMessage(content=msg.content))
            else:
                logger.warning("Unknown role in messages")

        # Run agent
        if not request.stream:
            lg_result = await agent.arun(lg_msg_lst)
            result = []
            for msg in lg_result["messages"]:
                if msg.content:
                    if isinstance(msg, AIMessage):
                        result.append({"role": "assistant", "content": msg.content})
                    elif isinstance(msg, ToolMessage):
                        result.append({"role": "tool", "content": msg.content})
                    elif isinstance(msg, HumanMessage):
                        result.append({"role": "user", "content": msg.content})
                    else:
                        logger.warning(f"Unknown message type {type(msg)}")
                        logger.warning(f"Unknown message {msg}")
            return ChatResponse(
                messages=result,
                news=lg_result["metadata"]["news"]
            )
        return StreamingResponse(agent.astream(lg_msg_lst, json_mode=True))

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
