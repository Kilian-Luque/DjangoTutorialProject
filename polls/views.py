from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.db.models import F
from django.utils import timezone

from .models import Choice, Question

class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future or without choices).
        """
        query_all = Question.objects.all()
        query_filter = Question.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')

        for question in query_all:
            if question.choice_set.count() == 0:
                query_filter = query_filter.exclude(pk=question.pk)

        return query_filter[:5]

class DetailView(generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet and the questions
        without choices.
        """
        query_all = Question.objects.all()
        query_filter = Question.objects.filter(pub_date__lte=timezone.now())

        for question in query_all:
            if question.choice_set.count() == 0:
                query_filter = query_filter.exclude(pk=question.pk)

        return query_filter

class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        # Avoid race condition with F() object
        selected_choice.votes = F('votes') + 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
