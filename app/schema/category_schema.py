from pydantic import BaseModel

class CategoryRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attribute = True

class CategoryCreate(BaseModel):
    name: str
    
    class Config:
        from_attribute = True

