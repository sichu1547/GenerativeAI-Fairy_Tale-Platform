from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import JsonResponse
from django import forms
from django.urls import reverse

from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

from google.cloud import texttospeech
import io
import pandas as pd
import openai

import os
from openai import OpenAI
from django.conf import settings

client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)

def index(request):
    return render(request, 'generator/index.html')

# GPT 시스템 역할 정의
system_roles = [
    "Make the entered story the beginning of a fairy tale, create a Korean sentence according to the entered content, connect the stories, and make the sentence end naturally with 100 tokens.",
    "Using the information you entered, make the middle part of the connected fairy tale end in Korean with 100 tokens.",
    "Using the information you entered, create the ending of the fairy tale with three connected lines of Korean context."
]

# 마지막 문장을 기반으로 질문 프롬프트 생성 함수
def generate_question_prompt(last_sentence, stage):
    prompt = f"앞서 생성된 마지막 문장에 있는 단어를 가지고 대답은 따로 하지말고 질문만 해\n{last_sentence}"
    question_response = generate_response(prompt, "role for generating question")
    question = f"{stage}/3\n{question_response}"
    return question

# GPT-3.5 API를 사용하여 응답 생성 함수
def generate_response(prompt, role, max_tokens=110):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": role},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        n=1,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def paginate_story(story, max_length=500):
    words = story.split()
    parts = []
    current_part = ""
    for word in words:
        if len(current_part) + len(word) + 1 > max_length:
            parts.append(current_part)
            current_part = word
        else:
            if current_part:
                current_part += " " + word
            else:
                current_part = word
    if current_part:
        parts.append(current_part)
    return parts

def create_story(request):
    if request.method == "POST":
        initial_story = request.POST.get('initial_story')
        story = request.POST.get('story', initial_story)
        generated_stories = request.POST.getlist('generated_stories', [])
        generated_images = request.POST.getlist('generated_images', [])
        stage = int(request.POST.get('stage', 0))
        user_input = request.POST.get('user_input', '')

        if stage > 0:
            story += " " + user_input

        if stage < 3:
            role = system_roles[stage]
            response = generate_response(story, role)
            story += " " + response
            generated_stories.append(response)
            
            image_url = generate_image(response)
            if not image_url:
                image_url = ""
            generated_images.append(image_url)

            last_sentence = response.split('.')[-1].strip()
            question_prompt = generate_question_prompt(last_sentence, stage + 1)

            context = {
                'story': story,
                'generated_stories': generated_stories,
                'stage': stage + 1,
                'question_prompt': question_prompt,
                'generated_images': generated_images
            }
            return render(request, 'generator/create_story.html', context)
        else:
            role = system_roles[2]
            final_prompt = f"{story}\n이 이야기를 어떻게 마무리할까요?"
            final_response = generate_response(final_prompt, role, max_tokens=300)
            story += " " + final_response
            final_story_parts = paginate_story(story)

            context = {
                'final_story': story,
                'final_story_parts': final_story_parts,
                'generated_stories': generated_stories,
                'generated_images': generated_images
            }
            return render(request, 'generator/story_result.html', context)
    else:
        return render(request, 'generator/create_story.html')
    
def generate_image(sentence):
    print('이미지 생성 중')
    api_key = settings.OPENAI_API_KEY_FOR_IMAGE_GEN
    client = OpenAI(api_key = api_key)
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"다음은 동화 내용이야: {sentence}. 이 내용을 기반으로 그림을 그려줘. 귀여운 그림체로 부드러운 색조와 간단한 형태를 사용해 그려줘.",
            #prompt=f"Here is the text of a fairy tale: {sentence}. Based on this text, create an illustration for the story. Draw in a hand-drawn style with soft colors, simplified shapes.",
            size="1024x1024",
            n=1,
            quality="standard",
            style="natural"
        )
        image_url = response.data[0].url
        return image_url

    except Exception as e:
        return ""