import os

from langchain_core.messages import HumanMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI

class GoogleAI:
    def __init__(self) -> None:
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        self.GOOGLE_MODEL = os.getenv("GOOGLE_MODEL")
        self.llm = ChatGoogleGenerativeAI(
            model=self.GOOGLE_MODEL,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2
        )

    def invoke(self, message: HumanMessage) -> BaseMessage:
        try:
            return_message = self.llm.invoke(
                input=[message]
            )
            return return_message
        except Exception as e:
            print(f"Error invoking Google AI: {e}")
            return None

    def order_message(self, image_url: str) -> HumanMessage:
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": """
                    Analyze this Vietnamese menu image and extract ONLY the main food dishes. Follow these rules:
                    
                    1. INCLUDE: Main dishes (rice dishes, noodle dishes, meat dishes, seafood dishes, vegetable dishes, soups)
                    2. EXCLUDE: Drinks (nước, trà, cà phê, bia, etc.), desserts, snacks, side items
                    3. Focus on complete meal items that would be ordered as main courses
                    4. If some dish names are partially visible or unclear, use your knowledge of Vietnamese cuisine to complete them appropriately
                    5. Return ONLY a clean JSON array of Vietnamese dish names
                    6. Do not include any explanation, code blocks, or markdown formatting
                    
                    Examples of what TO INCLUDE:
                    - Cơm (rice dishes)
                    - Bún, phở, miến (noodle dishes) 
                    - Thịt (meat dishes)
                    - Cá (fish dishes)
                    - Canh (soups)
                    - Rau (vegetable dishes)
                    
                    Examples of what TO EXCLUDE:
                    - Nước ngọt, nước suối
                    - Bia, rượu
                    - Trà, cà phê
                    - Chè, bánh ngọt
                    """,
                },
                {
                    "type": "text",
                    "text": """
                    Expected output format (example):
                    [
                        "Thịt luộc cà pháo",
                        "Cá điêu hồng chưng tương", 
                        "Bò xào rau cần",
                        "Canh khổ qua",
                        "Vịt kho gừng"
                    ]
                    """
                },
                {
                    "type": "image_url",
                    "image_url": image_url
                }
            ]
        )
        return message
