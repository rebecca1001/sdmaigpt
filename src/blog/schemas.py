from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, validator
from .validator import validate_width_and_height


class ToneOfVoice(str, Enum):

    """
    It includes all the predefined inputs for tone of voice
    """

    professional = "professional"
    conversational = "conversational"
    humorous = "humorous"
    empathic = "empathic"
    simple = "simple"
    academic = "academic"
    creative = "creative"


class OutputFormat(str, Enum):

    """
    It includes all the predefined inputs for output format
    """

    html = "html"
    markdown = "markdown"
    text = "text"


class QueryRequest(BaseModel):

    """
    This class defines the input fields
    """

    title: Optional[str] = ""
    keyword: Optional[str] = ""
    title_and_headings: Optional[str] = ""
    length: Optional[int] = 1750
    tone_of_voice: ToneOfVoice = ToneOfVoice.professional
    language: Optional[str] = "English"
    format: OutputFormat = OutputFormat.markdown
    spellings_format: Optional[str] = "American"
    project_id: str
    number_of_images: Optional[int] = 0
    width_of_image: Optional[int] = 512
    height_of_image: Optional[int] = 512
    version: Optional[str] = "test"

    @validator("width_of_image", always=True)
    def width_of_image_validator(cls, value, values):
        return validate_width_and_height(cls, value, values, type="Width")

    @validator("height_of_image", always=True)
    def height_of_image_validator(cls, value, values):
        return validate_width_and_height(cls, value, values, type="Height")


class ImageRequest(BaseModel):

    """
    This class defines the input fields
    """

    title: Optional[str] = ""
    headers: Optional[List] = []
    width_of_image: Optional[int] = 512
    height_of_image: Optional[int] = 512

    @validator("width_of_image", always=True)
    def width_of_image_validator(cls, value, values):
        return validate_width_and_height(cls, value, values, type="Width")

    @validator("height_of_image", always=True)
    def height_of_image_validator(cls, value, values):
        return validate_width_and_height(cls, value, values, type="Height")
