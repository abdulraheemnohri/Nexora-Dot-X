from typing import Any, AsyncIterator
import asyncio

class LiteRTEngine:
    """Real Python adapter for the current LiteRT-LM Engine API."""
    def __init__(self, model_path: str, max_output_tokens: int = 512):
        self.model_path=model_path
        self.max_output_tokens=max_output_tokens
        self.engine=None
        self.conversation=None

    async def load(self):
        try:
            from litert_lm import Engine
        except ImportError as exc:
            raise RuntimeError("LiteRT-LM is not installed. Install the [litert] extra.") from exc
        self.engine=Engine(self.model_path, max_num_tokens=self.max_output_tokens)
        self.conversation=self.engine.create_conversation(
            max_output_tokens=self.max_output_tokens,
            automatic_tool_calling=False,
        )
        return self

    async def unload(self):
        if self.engine is not None:
            delete=getattr(self.engine,"delete",None)
            if delete:
                result=delete()
                if asyncio.iscoroutine(result): await result
        self.engine=None
        self.conversation=None

    async def generate(self,prompt:str,**kwargs:Any)->str:
        if self.conversation is None: raise RuntimeError("LiteRT model is not loaded")
        response=self.conversation.send_message(prompt)
        if asyncio.iscoroutine(response): response=await response
        if hasattr(response,"text"): return response.text
        content=getattr(response,"content",None)
        if content:
            return "".join(getattr(x,"text","") for x in content)
        return str(response)

    async def stream(self,prompt:str,**kwargs:Any)->AsyncIterator[str]:
        if self.conversation is None: raise RuntimeError("LiteRT model is not loaded")
        stream=self.conversation.send_message_stream(prompt)
        if hasattr(stream,"__aiter__"):
            async for chunk in stream:
                text=getattr(chunk,"text",None)
                if text: yield text
                else:
                    for item in getattr(chunk,"content",[]) or []:
                        value=getattr(item,"text",None)
                        if value: yield value
        else:
            response=await stream if asyncio.iscoroutine(stream) else stream
            yield getattr(response,"text",str(response))

    async def health(self)->bool:
        return self.engine is not None and self.conversation is not None

    def metadata(self):
        return {"provider":"litert-lm","model_path":self.model_path,"loaded":self.engine is not None}
