from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse
from django import forms
from django.urls import reverse
from langchain_community.vectorstores import Chroma
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User
from google.cloud import texttospeech
import io
import pandas as pd
import openai
from .models import GenStory
from myaccount.models import Profile
import os
from openai import OpenAI
from django.conf import settings
import string
import json
import requests
from django.core.files.base import ContentFile

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
    "입력된 단어를 주제로 동화의 중간 부분을 한국어로 만들어주세요",
    "입력된 단어를 주제로 동화의 중간 부분을 앞 내용과 다르게 한국어로 만들어주세요",
    "입력한 정보를 넣어서 한국어로 세 줄로 연결된 동화의 결말을 만들어 보세요."
]

# 전체 이야기를 기반으로 질문 프롬프트 생성 함수
def generate_question_prompt(story, stage):
    prompt = f"이 동화의 마지막 부분을 기반으로 대답하지 말고 주관식으로 한가지 질문을 생성해 주세요.\n{story}"
    question_response = generate_response(prompt, "role for generating question")
    question = f"{stage}/3\n{question_response}"
    return question

# GPT-4o API를 사용하여 응답 생성 함수
def generate_response(prompt, role, max_tokens=110):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": role},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        n=1,
        temperature=0.8
    )
    content = response.choices[0].message.content.strip()
    
    # role이 system_roles[3]가 아닌 경우에만 문장이 끊기지 않도록 처리
    if role != system_roles[3]:
        sentences = content.split('. ')
        complete_content = '. '.join(sentences[:-1]) + '.' if len(sentences) > 1 else content
        return complete_content
    else:
        return content

def create_story(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")
    if request.method == "POST":
        # 최종 결과 TTS
        if request.POST.get('tts') == 'true':
            return generate_tts(request)
        
        initial_story = request.POST.get('initial_story', '')
        generated_stories = request.POST.getlist('generated_stories', [])
        generated_story_parts_json = request.POST.get('generated_story_parts', '[]')
        
        try:
            generated_story_parts = json.loads(generated_story_parts_json)
        except json.JSONDecodeError:
            generated_story_parts = []

        generated_images = request.POST.getlist('generated_images', [])
        stage = int(request.POST.get('stage', 0))
        user_input = request.POST.get('user_input', '')
        profile_id = request.session.get('selected_profile_id')
        
        if profile_id:
            profile = get_object_or_404(Profile, id=profile_id, user=request.user)
        else:
            profile = Profile.objects.get(id=settings.DEFAULT_PROFILE_ID)

        # 사용자 입력값을 이야기의 주요 키워드로 사용
        if stage > 0:
            story = " ".join(generated_stories) + f"참고 내용: {user_input}"
        else:
            story = initial_story + f" 참고 내용: {user_input}"

        # 스테이지가 3보다 작은 경우 이야기를 생성하는 단계를 진행
        if stage < 3:
            role = system_roles[stage]
            response = generate_response(story, role)

            generated_story = response.strip()

            # generated_stories에 생성된 이야기 추가
            generated_stories.append(generated_story + '\n\n\n')

            # generated_story_parts에 생성된 이야기 파트 추가
            generated_story_parts.append(generated_story)
            
            # 생성된 이야기를 바탕으로 이미지를 생성하고 리스트에 추가
            image_url = generate_image(generated_story_parts[-1])
            if not image_url:
                image_url = ""
            generated_images.append(image_url)

            # 전체 이야기에서 질문 프롬프트를 생성
            question_prompt = generate_question_prompt(" ".join(generated_stories), stage + 1)

            # 생성된 이야기, 이미지, 질문 프롬프트, 스테이지 정보를 컨텍스트로 전달하여 렌더링
            context = {
                'story': " ".join(generated_stories),
                'generated_stories': generated_stories,
                'generated_story_parts': json.dumps(generated_story_parts, ensure_ascii=False),
                'stage': stage + 1,
                'question_prompt': question_prompt,
                'generated_images': generated_images
            }
            return render(request, 'generator/create_story.html', context)
        else:
            # 스테이지가 3인 경우, 최종 이야기 결말을 생성 (+마지막 이미지 생성 추가)
            role = system_roles[3]
            final_prompt = f"{story}\n이 동화를 어떻게 마무리할까요?"
            final_response = generate_response(final_prompt, role, max_tokens=300)
            
            final_generated_story = final_response.strip()
            
            # generated_stories에 생성된 이야기 추가
            generated_stories.append(final_generated_story.strip() + '\n\n\n')
            
            # generated_story_parts에 생성된 이야기 파트 추가
            generated_story_parts.append(final_generated_story.strip())
           
            # 생성된 이야기를 바탕으로 이미지를 생성하고 리스트에 추가
            image_url = generate_image(generated_story_parts[-1])
            if not image_url:
                image_url = ""
            generated_images.append(image_url)
            
            # 최종 이야기 전체를 하나의 문자열로 결합
            final_story = " ".join(generated_stories)
            
            # db
            title_prompt = f"{final_story}\n이 이야기의 제목을 지어주세요"
            title_response = generate_response(title_prompt, role, max_tokens=300)   
            title = title_response.split('"')[1]
            user = request.user
            default_user = User.objects.get(id=settings.DEFAULT_USER_ID)
            if not user.is_authenticated:
                user = default_user
            
            thumbnail_url = generated_images[0].split(',')[0]
            if not thumbnail_url:
                thumbnail_url = 'static/images/default_image.jpg'
            file_path = save_final_story_to_database(final_story, profile, user, title, thumbnail_url)

            # 최종 이야기와 이를 분할한 파트, 생성된 이야기 및 이미지 리스트를 컨텍스트로 전달하여 렌더링
            context = {
                'final_story': final_story,
                'generated_stories': generated_stories,
                'generated_images': generated_images,
                'generated_story_parts': json.dumps(generated_story_parts, ensure_ascii=False),
                'file_path': file_path  # 파일 경로를 컨텍스트에 추가
            }
            return render(request, 'generator/story_result.html', context)
    else:
        # GET 요청인 경우 이야기 생성 페이지를 렌더링
        return render(request, 'generator/create_story.html')

def generate_image(sentence):
    # print('이미지 생성 중')
    # api_key = settings.OPENAI_API_KEY_FOR_IMAGE_GEN
    # client = OpenAI(api_key = api_key)
    
    # try:
    #     response = client.images.generate(
    #         model="dall-e-3",
    #         prompt=f"Create a cute and colorful children's book illustration. The scene should be inspired by the following sentence: '{sentence}'. Ensure the style is drawn with soft lines, bright and pastel colors, and a friendly, playful feel. The background should be detailed but not too complex, keeping it engaging but simple for children. Use a hand-drawn, cartoon-like style. The image should only consist of picture elements, NOT TEXT.",
    #         size="1024x1024",
    #         n=1,
    #         quality="standard",
    #         style="natural"
    #     )
    #     image_url = response.data[0].url
    #     print('성공')
    #     return image_url

    # except Exception as e:
    #     print('실패')
    return ""


def save_final_story_to_database(final_story, profile, user, title, thumbnail_url):
    try:
        filename = ''
        if thumbnail_url != 'static/images/default_image.jpg':
            response = requests.get(thumbnail_url)

            if response.status_code == 200:
                filename = f"{title}.png"
                content_file = ContentFile(response.content)
                
        Gen_Story = GenStory.objects.create(
            title = title,
            user = user,
            body=final_story,
            profile = profile
        )
        if filename != '':
            Gen_Story.thumbnail.save(filename, content_file) 
        Gen_Story.save()
    except Exception as e:
        print(f"Error saving to database: {e}")
    
def generate_tts(request):
    try:
        # Google TTS 클라이언트 설정
        client = texttospeech.TextToSpeechClient.from_service_account_json(settings.GOOGLE_APPLICATION_CREDENTIALS)
        

        # 선택된 목소리 가져오기
        selected_voice = request.POST.get('voice', 'ko-KR-Standard-A')
        text = request.POST.get('text', '')

        if text == 'full':
            text = request.POST.get('final_story', '')

        # TTS 요청 설정
        ssml_text = f"""<speak>{text}</speak>"""
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
        voice = texttospeech.VoiceSelectionParams(language_code="ko-KR", name=selected_voice, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        
        # TTS 요청 실행
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        
        # 음성 데이터를 메모리에 저장
        audio_stream = io.BytesIO(response.audio_content)
        
        # 음성 데이터를 HTTP 응답으로 반환
        return HttpResponse(audio_stream.getvalue(), content_type='audio/mpeg')
    
    except Exception as e:
        return HttpResponse(f"Error: {e}", status=500)
    