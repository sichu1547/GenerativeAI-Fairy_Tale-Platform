from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from reader.models import Story
from django.conf import settings

import re
import pdb
import sqlite3
import os
import mysql.connector

from django.http import HttpResponse
from google.cloud import texttospeech
import io
from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

class QuizView(View):
    m_context = {}
    path = './db.sqlite3'

    def get(self, request, id):
        keyword = request.GET.get('keyword', '')
            
        if 'quizzes' in QuizView.m_context:
            QuizView.m_context['keyword'] = keyword
        else:
            story = get_object_or_404(Story, id=id)

            if not story:
                return render(request, 'quiz/no_story.html')

            patterns = r'\r\n\r\n\r\n|\r\n\r\n \r\n|\r\n \r\n \r\n|\r\n \r\n\r\n'
            sentences = re.split(patterns, story.body)

            question, answer, example = self.generate_questions_with_gpt(sentences, id)
            self.save_question(id, question, answer)
            QuizView.m_context = {'quizzes': question, 'answer': answer, 'example': example, 'keyword': keyword, 'story': story}

        if 'tts' in request.GET:
            return self.generate_tts(request, id)
        
        return render(request, 'quiz/quiz.html', QuizView.m_context)
    
    def generate_tts(self, request, id):
        try:
            client = texttospeech.TextToSpeechClient.from_service_account_json('service_account.json')
            selected_voice = request.GET.get('voice', 'ko-KR-Standard-A')
            ssml_text = f"""<speak>{QuizView.m_context['quizzes'] + '<break time="1s"/>' + ''.join([f'{i+1}번. {item}<break time="1s"/>' for i, item in enumerate(QuizView.m_context['example'])])}</speak>"""

            synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
            voice = texttospeech.VoiceSelectionParams(language_code="ko-KR", name=selected_voice, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

            response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
            audio_stream = io.BytesIO(response.audio_content)

            return HttpResponse(audio_stream.getvalue(), content_type='audio/mpeg')
        except Exception as e:
            return HttpResponse(f"TTS Error: {e}", status=500)    

    def post(self, request, id):
        answer = request.POST.get('answer')
        correct_answer = request.POST.get('correct_answer')
        keyword = request.POST.get('keyword', '')
        if answer == "동화 리스트로 돌아가기":
            return redirect(f'/reader/search/?keyword={keyword}')
        else:
            if answer in correct_answer:
                result = "축하합니다🥳"
                QuizView.m_context = {}
            else:
                result = "틀렸습니다😢<br>다시 풀어보세요!".format(correct_answer)

        return render(request, 'quiz/quiz_result.html', {'result': result, 'quiz_id': id, 'keyword': keyword})

    def is_answer_asked(self, question):
        conn = mysql.connector.connect(
            host = settings.DB_HOST,
            user = settings.DB_USER,
            password = settings.DB_PASSWORD,
            database = settings.DB_NAME
        )   
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_history(
            id INTEGER PRIMARY KEY,
            story_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
        ''')
        conn.commit()

        cursor.execute('SELECT * FROM quiz_history WHERE question = %s', (question, ))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def save_question(self, story_id, question, answer):
        conn = mysql.connector.connect(
            host = settings.DB_HOST,
            user = settings.DB_USER,
            password = settings.DB_PASSWORD,
            database = settings.DB_NAME
        )   
        cursor = conn.cursor()
        cursor.execute('INSERT INTO quiz_history (story_id, question, answer) VALUES (%s, %s, %s)', (story_id, question, answer))
        conn.commit()
        conn.close()

    def generate_questions_with_gpt(self, paragraph, story_id):
        api_key = settings.OPENAI_API_KEY
        chat = ChatOpenAI(model="gpt-4o", openai_api_key=api_key)
        
        prompt = f"다음 문단을 읽고 최대한 간단하고 본문에 명시된 답변이 나오게 질문을 하나 만들고 그에 대한 정답 1개와 정답과 비슷한 보기를 정답을 포함해서 3개를 제시해라:\n\n{paragraph}"
        cnt = 0
        
        while cnt < 5:
            response = chat.invoke([HumanMessage(content=prompt)])
            lines = response.content.split('\n\n')
            lines = [re.sub(r'[###|%%%|\$\$\$|\*\*\*]', '', item).strip() for item in lines]
            
            try:
                question = lines[0].replace("질문: ", "")
                answer = lines[1].replace("정답: ", "")
                temp = lines[2].split('\n')
                example = [temp[i].split('. ')[1] for i in range(1, len(temp))]
                
                # 질문이 이미 존재하는지 확인하고 조건을 만족하면 리턴
                if not self.is_answer_asked(question):
                    return question, answer, example
            except IndexError:
                # 필요한 요소가 없을 경우 카운트 증가 및 다시 시도
                cnt += 1

        # 실패 시 기본값 리턴 (예외처리 필요 시)
        question = "퀴즈가 모두 소진되었습니다. 동화 리스트로 돌아가세요"
        answer = "동화 리스트로 돌아가기"
        example = ["동화 리스트로 돌아가기", "동화 리스트로 돌아가기", "동화 리스트로 돌아가기"]
        return question, answer, example       
        
def index(request):
    return render(request, 'quiz/quiz.html')