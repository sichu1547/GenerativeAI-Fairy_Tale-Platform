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
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")
    return render(request, 'generator/index.html')

# GPT 시스템 역할 정의
system_roles = [
    "입력된 이야기를 동화의 시작으로 만들고, 입력된 내용에 따라 한국어 문장을 만들어 이야기를 연결한 문장을 만들어 보세요.",
    "입력한 정보를 이용하여 연결된 동화의 중간 부분을 한국어로 만들어주세요",
    "입력한 정보를 이용하여 한국어로 세 줄로 연결된 동화의 결말을 만들어 보세요."
]

# 전체 이야기를 기반으로 질문 프롬프트 생성 함수
def generate_question_prompt(story, stage):
    prompt = f"이 동화의 마지막 부분을 기반으로 대답하지 말고 주관식으로 한가지 질문을 생성해 주세요.\n{story}"
    question_response = generate_response(prompt, "role for generating question")
    question = f"{stage}/3\n{question_response}"
    return question

# GPT-4 API를 사용하여 응답 생성 함수
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
    # 110 토큰으로 생성된 문장이 끊기지 않도록 최대한 완전한 문장을 반환
    content = response.choices[0].message.content.strip()
    sentences = content.split('. ')
    complete_content = '. '.join(sentences[:-1]) + '.' if len(sentences) > 1 else content
    return complete_content

# 이야기 분할 함수
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

def clean_story(story):
    return story.replace(',', '').replace(' ,', '').replace(', ', '').replace('..', '.').strip()

def create_story(request):
    if request.method == "POST":
        initial_story = request.POST.get('initial_story', '')
        generated_stories = request.POST.getlist('generated_stories', [])
        generated_images = request.POST.getlist('generated_images', [])
        stage = int(request.POST.get('stage', 0))
        user_input = request.POST.get('user_input', '')

        # 스테이지가 0보다 크면 사용자 입력을 이야기 뒤에 추가
        if stage > 0:
            story = " ".join(generated_stories) + " " + user_input
        else:
            story = initial_story + " " + user_input

        # 스테이지가 3보다 작은 경우, 이야기를 생성하는 단계를 진행
        if stage < 3:
            role = system_roles[stage]
            response = generate_response(story, role)
            
            # 사용자 입력을 generated_stories에 저장
            if stage > 0:
                generated_stories.append(user_input)
            generated_stories.append(response.strip('.')) # 문장 끝의 점을 제거하고 추가
            
            # 생성된 이야기를 바탕으로 이미지를 생성하고 리스트에 추가
            image_url = generate_image(response)
            if not image_url:
                image_url = ""
            generated_images.append(image_url)

            # 전체 이야기에서 질문 프롬프트를 생성
            question_prompt = generate_question_prompt(" ".join(generated_stories), stage + 1)

            # 생성된 이야기, 이미지, 질문 프롬프트, 스테이지 정보를 컨텍스트로 전달하여 렌더링
            context = {
                'story': clean_story(" ".join(generated_stories)), # 쉼표 문제 해결
                'generated_stories': generated_stories,
                'stage': stage + 1,
                'question_prompt': question_prompt,
                'generated_images': generated_images
            }
            return render(request, 'generator/create_story.html', context)
        else:
            # 스테이지가 3인 경우, 최종 이야기 결말을 생성
            role = system_roles[2]
            final_prompt = f"{story}\n이 이야기를 어떻게 마무리할까요?"
            final_response = generate_response(final_prompt, role, max_tokens=300)
            
            # 사용자 입력을 generated_stories에 저장
            if stage > 0:
                generated_stories.append(user_input)
            generated_stories.append(final_response.strip('.')) # 문장 끝의 점을 제거하고 추가
            
            # 최종 이야기 전체를 하나의 문자열로 결합하여 분할
            final_story = clean_story(" ".join(generated_stories)) # 쉼표 문제 해결
            final_story_parts = paginate_story(final_story)

            # 최종 이야기와 이를 분할한 파트, 생성된 이야기 및 이미지 리스트를 컨텍스트로 전달하여 렌더링
            context = {
                'final_story': final_story,
                'final_story_parts': final_story_parts,
                'generated_stories': generated_stories,
                'generated_images': generated_images
            }
            return render(request, 'generator/story_result.html', context)
    else:
        # GET 요청인 경우 이야기 생성 페이지를 렌더링
        return render(request, 'generator/create_story.html')

def generate_image(sentence):
    print('이미지 생성 중')
    api_key = settings.OPENAI_API_KEY_FOR_IMAGE_GEN
    client = OpenAI(api_key = api_key)
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"다음은 동화 내용이야: {sentence}. 이 내용을 기반으로 그림을 그려줘. 귀여운 그림체로 부드러운 색조와 간단한 형태를 사용해 그려줘.",
            size="1024x1024",
            n=1,
            quality="standard",
            style="natural"
        )
        image_url = response.data[0].url
        return image_url

    except Exception as e:
        return ""