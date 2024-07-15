from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from quiz.views import QuizView
import re
from django.db.models import Q
from django.http import HttpResponse
from google.cloud import texttospeech
import io
import sqlite3
from openai import OpenAI
import requests
from django.conf import settings
from django.core.files.base import ContentFile

# fairytales/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Story, LogEntry
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
import os

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from .models import Story
from myaccount.models import ReadingHistory, Profile
import random
 

def index(request):
    return render(request, 'reader/index.html')
def search(request):
    keyword = request.GET.get('keyword')
    search_type = request.GET.get('search_type', 'title')
    if keyword:
        if search_type == 'title':
            stories = Story.objects.filter(title__icontains=keyword)
        else:
            stories = Story.objects.filter(category__icontains=keyword)
    else:
        stories = Story.objects.all()      
         
    return render(request, 'reader/search_results.html', {'stories': stories, 'keyword': keyword})

def list(request):
    story_list = Story.objects.all()
    search_key = request.GET.get('keyword')
    if search_key :
        story_list = Story.objects.filter(title__contains=search_key)
    return render(request, 'reader/index.html', {'story_all': story_list})

def detail(request, id):
    print('======================================')
    story = get_object_or_404(Story, id=id)
    tag_list = story.tag.all()
    
    return render(request, 'reader/detail.html', {'story': story, 'tag_list': tag_list})

def search(request):
    keyword = request.GET.get('keyword')

    if keyword:
        # if search_type == 'title':
        #     stories = Story.objects.filter(title__icontains=keyword)
        # else:
        #     stories = Story.objects.filter(category__icontains=keyword)
        stories = Story.objects.filter(Q(title__icontains=keyword) | Q(category__icontains=keyword))
    else:
        stories = Story.objects.all()      

    return render(request, 'reader/search_results.html', {'stories': stories, 'keyword': keyword})

def generate_image(sentence):
    print('생성중')
    # api_key = settings.OPENAI_API_KEY
    # client = OpenAI(api_key = api_key)

    # try:
    #     response = client.images.generate(
    #         model="dall-e-3",
    #         prompt=f"다음은 동화 내용이야: {sentence}. 이 내용을 기반으로 그림을 그려줘. 귀여운 그림체로 부드러운 색조와 간단한 형태를 사용해 그려줘.",
    #         #prompt=f"Here is the text of a fairy tale: {sentence}. Based on this text, create an illustration for the story. Draw in a hand-drawn style with soft colors, simplified shapes.",
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


def story_detail(request, id):
    story = get_object_or_404(Story, id=id)
    profile_id = request.session.get('selected_profile_id')

    if profile_id:
        try:
            profile = get_object_or_404(Profile, id=profile_id, user=request.user)
            ReadingHistory.objects.get_or_create(user=request.user, profile=profile, story_title=story.title, story_id=story.id)
            print("Reading history saved successfully")
        except Exception as e:
            print(f"Error saving reading history: {e}")
    else:
        print("Profile ID not found in session")

    keyword = request.GET.get('keyword')
    sentences = story.body.split('\r\n\r\n\r\n') 
    
    # 이미지
    image_urls = [generate_image(sentences[0])] if sentences else []

    if 'tts' in request.GET:
        try:
            # Google TTS 클라이언트 설정
            client = texttospeech.TextToSpeechClient.from_service_account_json('service_account.json')

            # 선택된 목소리 가져오기
            selected_voice = request.GET.get('voice', 'ko-KR-Standard-A')
            text = request.GET.get('text', '')
            if text == 'full':
                text = story.title+'<break time="1s"/>'+story.body

            ssml_text = f"""<speak>{text}</speak>"""
            # ssml_text = f"""<speak>{story.title+'<break time="1s"/>'+story.body}</speak>"""

            # TTS 요청 설정
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

    previous_story_id = request.session.get('previous_story_id')

    if previous_story_id != id:
        QuizView.m_context = {}
        path = './database/quiz_history.db'
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM history')
        conn.commit()
        conn.close()    
        request.session['previous_story_id'] = id
        
    ########################################################################################################    
    # 장고 모델에서 모든 스토리 데이터 로드
    
    story = get_object_or_404(Story, id=id)
    
    stories = Story.objects.all()
    data = {
        '제목': [i.title for i in stories],
        '내용': [i.body for i in stories]
    }
    # 제목과 내용을 새로운 데이터프레임으로 저장
    df = pd.DataFrame(data)

    # 모델에서 id가 해당 동화인 데이터 가져오기
    # 제목만 따로 저장하기
    tale_title = story.title

    if not tale_title:
        return HttpResponse("Please provide a tale title.")  # 제목이 없으면 메시지 반환

    tfidf = TfidfVectorizer()
    dtm = tfidf.fit_transform(df['내용'])
    dtm = pd.DataFrame(dtm.todense(), columns=tfidf.get_feature_names_out())

    nn = NearestNeighbors(n_neighbors=6, algorithm='kd_tree')
    nn.fit(dtm)

    try:
        idx = df[df['제목'] == tale_title].index[0]
    except IndexError:
        return HttpResponse("Tale title not found.")  # 제목이 데이터베이스에 없으면 메시지 반환

    result = nn.kneighbors([dtm.iloc[idx]])
    random_value = random.randint(1,5)
    recommended_title = df['제목'].iloc[result[1][0][random_value]]
    
    story = get_object_or_404(Story, title=recommended_title)
    recommended_id = story.id
    

    return render(request, 'reader/story_detail.html', {'story': sentences, 'keyword': keyword, 'title': tale_title, 'id': id, 'image_urls': image_urls, 'rec_title':recommended_title, 'rec_id':recommended_id})
    ########################################################################################################    

def redirect_to_quiz(request, id):
    keyword = request.GET.get('keyword')

    return redirect(f"{reverse('quiz:quiz_view', args=[id])}?keyword={keyword}")

from django.http import JsonResponse

def generate_image_view(request):
    sentence = request.GET.get('sentence')
    if sentence:
        image_url = generate_image(sentence)
        return JsonResponse({'image_url': image_url})
    return JsonResponse({'error': 'No sentence provided'}, status=400)


# Initialize OpenAI embeddings, Chroma database, and ChatOpenAI model
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
persist_directory = os.path.join(settings.BASE_DIR, 'database')
database = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

chat = ChatOpenAI(model="gpt-4o")
retriever = database.as_retriever(search_kwargs={"k": 1})

memory = ConversationBufferMemory(memory_key="chat_history", input_key="question", output_key="answer", return_messages=True)

qa = ConversationalRetrievalChain.from_llm(
    llm=chat, retriever=retriever, memory=memory, 
    return_source_documents=True, output_key="answer")

@csrf_exempt
def answer_question(request):
    if request.method == 'POST':
        question = request.POST.get('question', None)
        story_id = request.POST.get('story_id', None)
        if question and story_id:
            story = get_object_or_404(Story, pk=story_id)

            # full_query = f"{story}에 대한 질문입니다.\n{question}"
            full_query = f"당신은 어린아이의 질문에 친절하게 답변해주는 선생님입니다. 동화 '{story}'에 대한 질문은 다음과 같고, 어린아이가 잘 이해할 수 있도록 대답해주세요.\n{question}"
        
            memory_content = memory.load_memory_variables({})

            # Perform the query
            result = qa({"question": full_query, "chat_history": memory_content["chat_history"]})

            # Output the answer obtained from LangChain
            answer = result["answer"]
            print(result)

            # Save to memory
            memory.save_context({"question": full_query}, {"answer": answer})

            # Save to the database
            save_to_database(story.title, question, answer)
            
            # print(memory.load_memory_variables({})["chat_history"])

            return JsonResponse({'answer': answer})

    return JsonResponse({'error': 'Invalid request'})

def save_to_database(story_title, question, answer):
    try:
        log_entry = LogEntry(story_title=story_title, question=question, answer=answer)
        log_entry.save()
    except Exception as e:
        print(f"Error saving to database: {e}")
        