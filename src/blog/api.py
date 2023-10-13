from fastapi import APIRouter, HTTPException
from src.blog.schemas import QueryRequest, ImageRequest
from src.blog import task

from src.blog.image_controller import ImageController

blog_router = APIRouter()


@blog_router.post("/generate_blog")
def generate_blog(request: QueryRequest):
    """
    It defines the endpoint to generate the final response.
    """
    try:
        print ('here')
        task.generate_task.delay(request.__dict__)
        return {"status": "Task is in progress!"}

    except HTTPException as e:
        raise e


@blog_router.post("/generate_feature_image")
def generate_image(request: ImageRequest):
    """
    It defines the endpoint to generate the title image.
    """
    try:
        content = ImageController(
            request.title,
            request.headers,
            request.width_of_image,
            request.height_of_image,
        )
        main_image, heading_images = content.generate_images()
        return {"main_image": main_image, "heading_images": heading_images}

    except:
        raise HTTPException(
            detail="Something went wrong in Image generation!", status_code=400
        )
