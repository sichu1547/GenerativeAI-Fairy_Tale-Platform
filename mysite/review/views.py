from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .forms import ReviewForm
from .models import Review
from reader.models import Story
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from myaccount.models import Profile

class ReviewView(LoginRequiredMixin, View):
    login_url = '/myaccount/login/'
    
    @method_decorator(login_required)
    def get(self, request, story_id):
        story = get_object_or_404(Story, id=story_id)
        form = ReviewForm()
        return render(request, 'review/write_review.html', {'form': form, 'story': story})

    @method_decorator(login_required)
    def post(self, request, story_id):
        story = get_object_or_404(Story, id=story_id)
        selected_profile_id = request.session.get('selected_profile_id')
        profile = get_object_or_404(Profile, id=selected_profile_id, user=request.user)        
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.story = story
            review.story_title = story.title
            review.profile = profile
                
            review.save()
            return redirect('review:review_success')
        return render(request, 'review/write_review.html', {'form': form, 'story': story})
    
from django.views.generic import ListView

class StoryListView(ListView):
    model = Story
    template_name = 'reader/story_list.html'
    context_object_name = 'stories'    
    
class ReviewListView(View):
    def get(self, request, profile_id):
        profile = get_object_or_404(Profile, id=profile_id, user=request.user)
        if profile:
            reviews = Review.objects.filter(user=request.user, profile_id=profile)
        else:
            reviews = Review.objects.filter(user=request.user)
        return render(request, 'review/review_list.html', {'reviews': reviews})

class ReviewDeleteView(DeleteView):
    model = Review
    template_name = 'review/review_confirm_delete.html'
    success_url = reverse_lazy('review:review_list')

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)