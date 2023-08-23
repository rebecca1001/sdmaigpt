from celery import Celery
from src.config import Config

from src.blog.blog_controller import BlogController

celery = Celery(
    __name__, broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND
)


@celery.task(rate_limit="1/m")
def generate_task(request):
    content = BlogController(
        request["title"],
        request["keyword"],
        request["title_and_headings"],
        request["length"],
        request["tone_of_voice"],
        request["language"],
        request["format"],
        request["spellings_format"],
        request["project_id"],
        request["number_of_images"],
        request["width_of_image"],
        request["height_of_image"],
        request["version"],
    )

    response = content.generate_response()

    return response
