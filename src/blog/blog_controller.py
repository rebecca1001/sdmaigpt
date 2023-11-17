import re
import openai
import requests
import time
import json

from fastapi import HTTPException

from src.blog.image_controller import ImageController
from src.blog.schemas import OutputFormat
from src.config import Config

leonardo_api_key = Config.LEONARDO_API_KEY
leonardo_model_id = Config.LEONARDO_MODEL_ID
openai.api_key = Config.OPENAI_API_KEY


OUTLINE_GENERATE_PROMPT = """
Generate blog post outline with section and subsection titles.
Make sure to only output outline and nothing else. 
Generate BLOG_SUBSECTION_COUNT subsections in total.
"""

SYSTEM_PROMPT = """
I Want You To Act As A Content Writer Very Proficient SEO Writer Writes Fluent English.
First, Create a Table. In the table, write the article outline, including at least 15 headings and subheadings. Ensure the blog title is the only title in H1, and the subheadings must be H2 or H3 only.
Now, let's proceed to write the article, heading by heading. Do not ignore: When writing the article, write the headings using Markdown language and ensure the headings are the same H tags as the article outline in the first table.
Write a detailed and comprehensive 2000-word 100% Unique, SEO-optimized, Human-Written article in English that covers the topic provided in the Prompt. Use fully detailed paragraphs that engage the reader, writing 400 - 500 words after each heading and subheading.
Write The article In Your Own Words Rather Than Copying And Pasting From Other Sources. Consider perplexity and burstiness when creating content, ensuring high levels of both without losing specificity or context.
Write In A Conversational Style As Written By A Human (Use An Informal Tone, Utilize Personal Pronouns, Keep It Simple, Engage The Reader, Use The Active Voice, Keep It Brief, Use Rhetorical Questions, and Incorporate Analogies And Metaphors).
End with a conclusion paragraph

Please follow this output format:
 - Write article outline plain text table output.
 - Write blog content in html format within <body> tag and use only <body>, <h1>, <h2>, <h3>, <p> tags.
 - Do not include any template or placeholder content.
 - Do not include any html attributes.
 - Write </body> tag and write _THE_END_ at the end of the entire blog generation.
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
        try:

            print ('_' * 100)
            print ('get_openai_full_result')
            print (system_prompt)
            print (prompt)
            print ('_' * 100)

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

                if 'THE_END' not in res:
                    res = res.replace('</body>', '')

                messages = messages + [{
                    "role": "assistant",
                    "content": res
                }]

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

            if not self.title:
                title_prompt = f"""
Write one blog title with the following information.

Keyword: "{self.keyword or ""}"
Tone of Voice: {self.tone_of_voice}
Language: {self.language}
Spellings Format: {self.spellings_format}

Return only title and nothing else.
Title should be between 20~100 characters and should be SEO optimized.
                """
                title = self.get_openai_response([{
                    "role": "user",
                    "content": title_prompt,
                }])
                self.title = title

            prompt = f"""
    Now Write An Article On This Topic "{self.title or self.keyword}"
            """

            system_prompt = SYSTEM_PROMPT.replace('BLOG_TITLE', self.title)

            blog = self.get_openai_full_result("", system_prompt + prompt)

            blog = '<body' + blog.split('<body')[-1]

            FAQ_PROMPT = """
- Generate an FAQ of 5 questions and answers based on the user provided content
- write _THE_END_ outside of the body tag when generation is finished
- Output as JSON format as following
[
{
    "QUestion": "...Question...",
    "Answer": "...Answer..."
},
...
]
            """

            faq = self.get_openai_full_result(FAQ_PROMPT, blog)

            META_PROMPT = """
Act as a copywriter and write a clickbait meta description of a minimum of 150 characters for the following topic and the description must not exceed 160 characters.
- Suggest a meta description based on the user provided content, make it user-friendly and with a call to action
- write as a plain text
- write _THE_END_ outside of the body tag when generation is finished
            """

            meta_description = self.get_openai_full_result(META_PROMPT, blog)

            bubble_body = {
                "seo_title": self.title.strip(),
                "content": blog,
                "frequently_asked_questions": json.loads(faq),
                "meta_description": meta_description,
                "project_id": self.project_id,
                "request_word": self.title or self.keyword or self.title_and_headings,
                "heading_images_prompt": self.headings,
                "main_image_url": self.main_image,
                "header_images_url": self.headings_images,
            }
            print (bubble_body)


            requests.post(
                "https://rebecca-29449.bubbleapps.io/api/1.1/wf/article",
                json=bubble_body,
            )

            return {
                "message": "Blog generated successfully",
                "title": self.title or self.keyword or self.title_and_headings,
                "project_id": self.project_id
            }
        except:
            requests.post(
                "https://rebecca-29449.bubbleapps.io/api/1.1/wf/generation-fail",
                json={ "project_id": self.project_id },
            )

            return {
                "message": "Blog generation failed",
                "project_id": self.project_id
            }
