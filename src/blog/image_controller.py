import time
from typing import List
from fastapi import HTTPException
import openai
import requests


class ImageController:
    def __init__(
        self,
        title: str,
        headers: List[str],
        width_of_image: int,
        height_of_image: int,
    ) -> None:
        self.title = title
        self.headers = headers
        self.width_of_image = width_of_image
        self.height_of_image = height_of_image

    def call_openai(self, prompt, model="gpt-4", temperature=0.8):
        """
        It is used to call openai and get response from it
        """

        try:
            response = openai.ChatCompletion.create(
                model=model, messages=prompt, temperature=temperature
            )

            # Extract desired output from JSON object
            content = response["choices"][0]["message"]["content"]
        except:
            try:
                response = openai.ChatCompletion.create(model=model, messages=prompt)

                # Extract desired output from JSON object
                content = response["choices"][0]["message"]["content"]
            except:
                raise HTTPException(detail="GPT error", status_code=400)

        return content

    def image_prompt_generation(self):
        messages = [
            {
                "role": "system",
                "content": "Act as a DALLE-2 prompt generator for image generation. You will be provided with the title and resoltuion and your task is to generate brief and enhanced prompt that can guide the image generator to generate the image. Include specifications like realistic, high quality, etc. in all the prompts. I want to generate the image for my blog so adjust the prompt accordingly considering the blog title. In the prompt do not mention that it is for the blog generation. For example, Title: Introduction to python programming language\nResolution: 512 x 512\nPrompt: Generate a high-quality, realistic 512 x 512 image featuring symbolic icons related to the Python programming language, such as a python snake and a coding terminal. This image is intended to serve as an attention-grabbing introduction to a blog post about Python programming.",
            },
            {
                "role": "user",
                "content": f"Title: {self.title}",
            },
        ]

        return self.call_openai(messages)

    def headings_image_prompt_generation(self, heading):
        messages = [
            {
                "role": "system",
                "content": "Act as a DALLE-2 prompt generator for image generation. You will be provided with the an outline and your task is to generate detailed and enhanced prompt for outline that can guide the image generator to generate the image. The prompt must have at least 30 words. Include specifications like realistic, high quality, etc. in all the prompts. I want to generate the images for my blog so adjust the prompt accordingly. In the prompt do not mention that it is for the blog generation. These images are intended to serve as attention-grabbing images for those who read the blog.",
            },
            {
                "role": "user",
                "content": f"Heading: {heading}",
            },
        ]

        return self.call_openai(messages)

    def generate_feature_image(self, prompt):
        url = "https://cloud.leonardo.ai/api/rest/v1/generations"

        payload = {
            "prompt": prompt,
            "negative_prompt": "cartoon, 2d, sketch, drawing, anime, open mouth, nudity, naked, nsfw, helmet, head gear, close up, blurry eyes, two heads, two faces, plastic, Deformed, blurry, bad anatomy, bad eyes, crossed eyes, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands, missing limb, blurry, floating limbs, disconnected limbs, malformed hands, blur, out of focus, long neck, long body, mutated hands and fingers, out of frame, blender, doll, cropped, low-res, close-up, poorly-drawn face, out of frame double, blurred, ugly, disfigured, too many fingers, deformed, repetitive, black and white, grainy, extra limbs, bad anatomyHigh pass filter, airbrush, zoomed, soft light, deformed, extra limbs, extra fingers, mutated hands, bad anatomy, bad proportions , blind, bad eyes, ugly eyes, dead eyes, blur, vignette, out of shot, out of focus, gaussian, closeup, monochrome, grainy, noisy, text, writing, watermark, logo, oversaturation,over saturation,over shadow",
            "modelId": "a097c2df-8f0c-4029-ae0f-8fd349055e61",
            "width": self.width_of_image,
            "height": self.height_of_image,
            "num_images": 1,
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer a28981f1-3f37-4a7f-bb4e-ee46334ee732",
        }
        response = requests.post(url, json=payload, headers=headers)

        image_id = response.json()

        image_url = image_id["sdGenerationJob"]["generationId"]

        url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{image_url}"

        headers = {
            "accept": "application/json",
            "authorization": "Bearer a28981f1-3f37-4a7f-bb4e-ee46334ee732",
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

    def generate_images(self):
        try:
            main_image_url = ""
            if self.title:
                main_image_prompt = self.image_prompt_generation()
                main_image_url = self.generate_feature_image(main_image_prompt)

            urls_for_heading = []
            if self.headers:
                headings = self.headers

                for heading in headings:
                    headings_prompt = self.headings_image_prompt_generation(heading)
                    urls_for_heading.append(
                        self.generate_feature_image(headings_prompt)
                    )
        except:
            main_image_url = ""
            urls_for_heading = []
        return main_image_url, urls_for_heading
