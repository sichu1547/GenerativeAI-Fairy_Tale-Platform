from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse
from django import forms
from django.urls import reverse
from langchain_community.vectorstores import Chroma

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
    "입력된 이야기에 이어서 동화의 중간 부분을 한국어로 만들어 보세요.",
    "입력된 이야기에 이어서 한국어로 세 줄로 연결된 동화의 결말을 만들어 보세요."
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
    content = response.choices[0].message.content.strip()
    
    # role이 system_roles[2]가 아닌 경우에만 문장이 끊기지 않도록 처리
    if role != system_roles[2]:
        sentences = content.split('. ')
        complete_content = '. '.join(sentences[:-1]) + '.' if len(sentences) > 1 else content
        return complete_content
    else:
        return content

def create_story(request):
    if request.method == "POST":
        # 최종 결과 TTS
        if request.POST.get('tts') == 'true':
            return generate_tts(request)
        
        initial_story = request.POST.get('initial_story', '')
        generated_stories = request.POST.getlist('generated_stories', [])
        generated_story_parts_json = request.POST.get('generated_story_parts', '[]')
        generated_story_parts = json.loads(generated_story_parts_json)
        generated_images = request.POST.getlist('generated_images', [])
        stage = int(request.POST.get('stage', 0))
        user_input = request.POST.get('user_input', '')
        profile_id = request.session.get('selected_profile_id')
        profile = get_object_or_404(Profile, id=profile_id, user=request.user)

        # 스테이지가 0보다 크면 사용자 입력을 이야기 뒤에 추가
        if stage > 0:
            story = " ".join(generated_stories) + " " + user_input
        else:
            story = initial_story + " " + user_input

        # 스테이지가 3보다 작은 경우, 이야기를 생성하는 단계를 진행
        if stage < 3:
            role = system_roles[stage]
            response = generate_response(story, role)
        
            generated_story = user_input + " " + response.strip()
            
            # generated_stories에 생성된 이야기 추가
            generated_stories.append(generated_story.strip())
            
            # 중복이 없도록 generated_story_parts에 생성된 이야기 파트 추가
            if generated_story.strip() not in generated_story_parts:
                generated_story_parts.append(generated_story.strip())
            
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
                'generated_story_parts': json.dumps(generated_story_parts),
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
            
            final_generated_story = user_input + " " + final_response.strip()
            
            # generated_stories에 생성된 이야기 추가
            generated_stories.append(final_generated_story.strip())
            
            # 중복이 없도록 generated_story_parts에 생성된 이야기 파트 추가
            if final_generated_story.strip() not in generated_story_parts:
                generated_story_parts.append(final_generated_story.strip())
           
            
            # 최종 이야기 전체를 하나의 문자열로 결합하여 분할
            final_story = " ".join(generated_stories)
            
            # db
            title_prompt = f"{final_story}\n이 이야기의 제목을 지어주세요"
            title_response = generate_response(title_prompt, role, max_tokens=300)   
            title = title_response.split('"')[1]
            file_path = save_final_story_to_database(final_story, profile, request.user, title)

            # 최종 이야기와 이를 분할한 파트, 생성된 이야기 및 이미지 리스트를 컨텍스트로 전달하여 렌더링
            context = {
                'final_story': final_story,
                'generated_stories': generated_stories,
                'generated_images': generated_images,
                'generated_story_parts': json.dumps(generated_story_parts),
                'file_path': file_path  # 파일 경로를 컨텍스트에 추가
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
            prompt=f"Create a cute and colorful children's book illustration. The scene should be inspired by the following sentence: '{sentence}'. Ensure the style is drawn with soft lines, bright and pastel colors, and a friendly, playful feel. The background should be detailed but not too complex, keeping it engaging but simple for children. Use a hand-drawn, cartoon-like style. The image should only consist of picture elements, NOT TEXT.",
            size="1024x1024",
            n=1,
            quality="standard",
            style="natural"
        )
        image_url = response.data[0].url
        return image_url

    except Exception as e:
        return ""
    #return ""

def save_final_story_to_database(final_story, profile, user, title):
    try:
        Gen_Story = GenStory.objects.create(
            title = title,
            user = user,
            body=final_story,
            profile = profile
        )
        Gen_Story.save()
    except Exception as e:
        print(f"Error saving to database: {e}")
    
def generate_tts(request):
    # print(request.POST)
    try:
        # Google TTS 클라이언트 설정
        client = texttospeech.TextToSpeechClient.from_service_account_json('service_account.json')
        

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