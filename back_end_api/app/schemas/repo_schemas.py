from pydantic import BaseModel

#tra ve du lieu danh sach bai viet sau khi goi gemini
class PostResponse(BaseModel):
    title: str
    content: str