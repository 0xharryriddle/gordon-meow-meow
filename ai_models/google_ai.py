import os

from langchain_core.messages import HumanMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI

class GoogleAI:
    def __init__(self) -> None:
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        self.GOOGLE_MODEL = os.getenv("GOOGLE_MODEL")
        self.llm = ChatGoogleGenerativeAI(model=self.GOOGLE_MODEL)

    def invoke(self, message: HumanMessage) -> BaseMessage:
        return self.llm.invoke([message])

    def order_message(self, image_url: str) -> HumanMessage:
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": "Give me only the array of foods in the image, does not include anything else. I need to get the js array only and does not need to put it in a variable or a code block in markdown. There are some names of foods are lacking, nếu có thể hãy hoàn thiện giúp.",
                },
                {
                    "type": "image_url",
                    "image_url": image_url
                }
            ]
        )
        return message
    