from django.shortcuts import render
from django.views import View
from .models import ReaderStory
from konlpy.tag import Okt
import random
import re
#import pdb
class QuizView(View):
    def get(self, request):
        story = ReaderStory.objects.first()
        #story = ReaderStory.objects.using('story').first()
        if not story:
            return render(request, 'quiz/no_story.html') 
        paragraphs = story.body.split('\n\n')  # 문단으로 분리
        quizze = [self.create_quiz_sentence(p) for p in paragraphs]
    
        for story, _, _ in quizze:
            quizzes = story.split('\r\n\r\n')   
        answer = quizze[0][1]      
        example = quizze[0][2]  
        context = {'quizzes': quizzes, 'answer' : answer, 'example' : example}
        #pdb.set_trace()
        return render(request, 'quiz/quiz.html', context)

    def post(self, request):
        answer = request.POST.get('answer')
        correct_answer = request.POST.get('correct_answer')

        if answer == correct_answer:
            result = "정답입니다!"
        else:
            result = f"틀렸습니다. 정답은 {correct_answer}입니다."

        return render(request, 'quiz/quiz_result.html', {'result': result})

    def extract_nouns(self, sentence):
        okt = Okt()
        nouns = okt.nouns(sentence)
        filtered_nouns = [noun for noun in nouns if self.is_valid_noun(noun) and len(noun) > 1]
        
        return filtered_nouns
    
    def is_valid_noun(self, word):
        return bool(re.search(r'[가-힣]', word))
    
    def create_quiz_sentence(self, paragraph):
        nouns = self.extract_nouns(paragraph)
        if not nouns:
            return paragraph, None, []
        chosen_noun = random.choice(nouns)
        other_nouns = list(set([n for n in nouns if n != chosen_noun]))
        other_nouns = random.sample(other_nouns, min(2, len(other_nouns)))
        quiz_sentence = paragraph.replace(chosen_noun, "____", 1)
        choices = [chosen_noun] + other_nouns
        random.shuffle(choices)
        return quiz_sentence, chosen_noun, choices

