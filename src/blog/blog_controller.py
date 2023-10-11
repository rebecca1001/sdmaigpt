import re
import openai
import requests
import time

from fastapi import HTTPException

from src.blog.image_controller import ImageController
from src.blog.schemas import OutputFormat
from src.config import Config

leonardo_api_key = Config.LEONARDO_API_KEY
leonardo_model_id = Config.LEONARDO_MODEL_ID
openai.api_key = Config.OPENAI_API_KEY


SYSTEM_PROMPT = """
 - please generate a blog post based on user's given information. Ensure that the content is engaging, informative, and relevant to the provided keyword.
 - Use the specified tone of voice and language.
 - Include the headings as mentioned and format the blog according to the chosen format.
 - Make sure to follow the spellings format and include the specified number of images with the provided dimensions.
 - Write blog in html format and only <body> section
 - Write AI image generation prompt in alt attribute of image tag without any indicator, write IMAGE_SRC_[index_number] in image src attribute, and self close img tag
 - Do not include any template words/sections. inside square brackets
 - Do not include more than 4 images in the entire blog
 - Make sure each paragraphs are more than 3 sentances
 - write _THE_END_ outside of the body tag when generation is finished
"""

class BlogController:
    def __init__(
        self,
        title: str,
        keyword: str,
        title_and_headings: str,
        length: int,
        tone_of_voice: str,
        language: str,
        format: str,
        spellings_format: str,
        project_id: int,
        number_of_images: int,
        width_of_image: int,
        height_of_image: int,
        version: str,
    ) -> None:
        self.title = title
        self.keyword = keyword
        self.title_and_headings = title_and_headings
        self.spellings_format = spellings_format
        self.introduction = ""
        self.improved_title = ""
        self.outlines = ""
        self.body_paragraphs = ""
        self.conclusion = ""
        self.faq = []
        self.length = length
        self.tone_of_voice = tone_of_voice
        self.language = language
        self.format = format
        self.meta_description = ""
        self.project_id = project_id
        self.response = {}
        self.number_of_images = number_of_images
        self.main_image = ""
        self.headings_images = []
        self.headings = []
        self.prompt = ""
        self.width_of_image = width_of_image
        self.height_of_image = height_of_image
        self.version = version

    def generate_image(self, prompt):
        url = "https://cloud.leonardo.ai/api/rest/v1/generations"

        payload = {
            "prompt": prompt,
            "negative_prompt": "cartoon, 2d, sketch, drawing, anime, open mouth, nudity, naked, nsfw",
            "modelId": leonardo_model_id,
            "width": self.width_of_image,
            "height": self.height_of_image,
            "num_images": 1,
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {leonardo_api_key}",
        }
        response = requests.post(url, json=payload, headers=headers)

        image_id = response.json()

        image_url = image_id["sdGenerationJob"]["generationId"]

        url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{image_url}"

        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {leonardo_api_key}",
        }

        response = requests.get(url, headers=headers)
        output = response.json()
        image_link = image_url
        for _ in range(3):
            if output["generations_by_pk"]["status"] == "COMPLETE":
                image_link = output["generations_by_pk"]["generated_images"][0]["url"]
                break
            else:
                time.sleep(5)
                response = requests.get(url, headers=headers)
                output = response.json()

        return image_link


    def get_openai_response(self, messages):
        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=messages,
            stream=True
        )

        result = ''

        for chunk in response:
            if chunk["choices"][0]["finish_reason"]:
                break
            substr = chunk["choices"][0]["delta"]["content"]
            result = result + substr
            print (substr, end="")

        return result


    def get_openai_full_result(self, system_prompt, prompt):
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        result = ''

        while 'THE_END' not in result:
            res = self.get_openai_response(messages)
            messages = messages + [{ "role": "user", "content": "continue" }]
            result = result + res

        result = result.replace(r'_THE_END_', '')

        img_entries = re.findall('<img.*src="(IMAGE_SRC_\d?)".*alt="(.+?)".*\/?>', result)

        for item in img_entries:
            print ('generating image', item[1])
            img_link = self.generate_image(item[1])
            print (img_link)
            result = result.replace(item[0], img_link)

        return result


    def generate_blog(self):
        system_prompt = SYSTEM_PROMPT.replace('NO_OF_IMAGES', self.number_of_images)
        prompt = f"""
            Title: "{self.title or "[Title of the blog]"}"
            Keyword: "{self.keyword or "[Keywords of the blog]"}"
            Length: {self.length} words
            Tone of Voice: {self.tone_of_voice}
            Language: {self.language}
            Spellings Format: {self.spellings_format}
        """

        blog = self.get_openai_full_result(system_prompt, prompt)

        bubble_body = {
            "seo_title": self.improved_title.strip(),
            "content": blog,
            "frequently_asked_questions": "",
            "meta_description": "",
            "project_id": self.project_id,
            "request_word": self.title or self.keyword or self.title_and_headings,
            "heading_images_prompt": self.headings,
            "main_image_url": self.main_image,
            "header_images_url": self.headings_images,
        }

        requests.post(
            "https://rebecca-29449.bubbleapps.io/api/1.1/wf/article",
            json=bubble_body,
        )

        return {
            "message": "Blog generated successfully",
            "title": self.title or self.keyword or self.title_and_headings,
            "project_id": self.project_id
        }
