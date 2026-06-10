from pydantic import BaseModel
from datetime import datetime
from typing import Optional
# tên mục và mô tả mục cua bai viet
class Section(BaseModel):
    title: str
    desc: str
# A Pydantic request body for creating posts from the client
class PostCreate(BaseModel):
    titles: list[str]
    style: str
    sections: list[Section]
    #token: str(authentication token from client)

class PostHistoryResponse(BaseModel):
    id: int
    post_id: int
    title: str
    prompt: Optional[str]
    content: Optional[str]
    status: str
    changed_at: datetime

    class Config:
        from_attributes = True
