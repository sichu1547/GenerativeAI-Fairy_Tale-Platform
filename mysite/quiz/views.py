from django.shortcuts import render, get_object_or_404
from django.views import View
from .models import ReaderStory
from django.conf import settings

import re
import pdb
import sqlite3
import os

from django.http import HttpResponse
from google.cloud import texttospeech
import io

from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage#, AIMessage
#from langchain.memory import ConversationBufferMemory
class QuizView(View):
    m_context = {}
    path = './database/quiz_history.db'

    def get(self, request, id):
        keyword = request.GET.get('keyword', '')
            
        if 'quizzes' in QuizView.m_context:
            QuizView.m_context['keyword'] = keyword
        else:
            story = get_object_or_404(ReaderStory, id=id)

            if not story:
                return render(request, 'quiz/no_story.html')

            paragraphs = story.body.split('\n\n')
            sentences = []
            for paragraph in paragraphs:
                sentences.extend(re.split(r'(?<=\.) ', paragraph))

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
            return HttpResponse(f"Error: {e}", status=500)    

    def post(self, request, id):
        answer = request.POST.get('answer')
        correct_answer = request.POST.get('correct_answer')
        keyword = request.POST.get('keyword', '')

        if answer == correct_answer:
            result = "정답입니다!"
            QuizView.m_context = {}
        else:
            result = f"틀렸습니다. 정답은 {correct_answer}입니다."

        return render(request, 'quiz/quiz_result.html', {'result': result, 'quiz_id': id, 'keyword': keyword})

    def is_answer_asked(self, question):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS history(
            id INTEGER PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
        ''')
        conn.commit()

        cursor.execute('SELECT * FROM history WHERE question = ?', (question, ))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def save_question(self, story_id, question, answer):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO history (story_id, question, answer) VALUES (?, ?, ?)', (story_id, question, answer))
        conn.commit()
        conn.close()

    def generate_questions_with_gpt(self, paragraph, story_id):
        api_key = settings.OPENAI_API_KEY
        # api_key = os.getenv('OPENAI_API_KEY')
        chat = ChatOpenAI(model="gpt-4o", openai_api_key=api_key)

        # memory = ConversationBufferMemory(memory_key="chat_history", input_key="question", output_key="answer", return_messages=True)

        # conn = sqlite3.connect(self.path)
        # cursor = conn.cursor()
        # cursor.execute('SELECT question, answer FROM history WHERE story_id = ?', (story_id,))
        # db_history = cursor.fetchall()
        # conn.close()

        # for message in db_history:
        #     memory.chat_memory.add_message(HumanMessage(content=message[0]))
        #     memory.chat_memory.add_message(AIMessage(content=message[1]))
        
        prompt = f"다음 문단을 읽고 최대한 간단하고 본문에 명시된 답변이 나오게 질문을 하나 만들고 그에 대한 정답 1개와 정답과 비슷한 보기를 정답을 포함해서 3개를 제시해라:\n\n{paragraph}"
        response = chat(messages=[HumanMessage(content=prompt)])

        lines = response.content.split('\n\n')     
        question = lines[0].replace("질문: ", "")
        cnt = 0
        while self.is_answer_asked(question) and cnt < 5:
            cnt += 1
            response = chat(messages=[HumanMessage(content=prompt)])
            lines = response.content.split('\n\n')     
            question = lines[0].replace("질문: ", "")

        lines = [re.sub(r'[###|%%%|\$\$\$|\*\*\*]', '', item).strip() for item in lines]
        question = lines[0].replace("질문: ", "")
        answer = lines[1].replace("정답: ", "")
        temp = lines[2].split('\n')
        example = []

        for i in range(1, len(temp)):
            example.append(temp[i].split('. ')[1])

        return question, answer, example          
        
def index(request):
    return render(request, 'quiz/quiz.html')