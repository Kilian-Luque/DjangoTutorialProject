from django.test import TestCase, LiveServerTestCase

from selenium.webdriver import Chrome
from selenium.webdriver.support.wait import WebDriverWait

# Create your tests here.
import datetime, time
from django.utils import timezone
from django.urls import reverse

from .models import Question, Choice

class QuestionModelTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)


def create_question(question_text, days):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)

def create_question_with_choices(question_text, days, choices):
    """
    Create a question with the given `question_text` published, the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published) and
    the given `choices`.
    """
    time = timezone.now() + datetime.timedelta(days=days)
    question = Question.objects.create(question_text=question_text, pub_date=time)

    for choice in choices:
        question.choice_set.create(choice_text=choice, votes=0)

    return question


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question_without_choices(self):
        """
        Questions without choices aren't displayed on
        the index page.
        """
        create_question(
            question_text="Past question without choices.",
            days=-30
        )
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question_with_choices(self):
        """
        The index view displays past questions with choices.
        """
        create_question_with_choices(
            question_text="Past question with choices.",
            days=-30,
            choices=["Choice 1", "Choice 2", "Choice 3"]
        )
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Past question with choices.")
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question with choices.>']
        )

    def test_future_question_without_choices(self):
        """
        Questions without choices with a pub_date in the future
        aren't displayed on the index page.
        """
        create_question(
            question_text="Future question without choices.",
            days=30
        )
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_with_choices(self):
        """
        Questions with choices with a pub_date in the future
        aren't displayed on the index page.
        """
        create_question_with_choices(
            question_text="Future question with choices.",
            days=30,
            choices=["Choice 1", "Choice 2", "Choice 3"]
        )
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_and_past_question_with_choices(self):
        """
        Even if both past and future questions with choices exist,
        only past questions with choices are displayed.
        """
        create_question_with_choices(
            question_text="Past question with choices.",
            days=-30,
            choices=["Choice 1", "Choice 2", "Choice 3"]
        )
        create_question_with_choices(
            question_text="Future question with choices.",
            days=30,
            choices=["Choice 1", "Choice 2", "Choice 3"]
        )
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question with choices.>']
        )

    def test_two_past_questions_with_choices(self):
        """
        The questions index page may display multiple questions
        with choices.
        """
        create_question_with_choices(
            question_text="Past question with choices 1.",
            days=-30,
            choices=["Choice 1", "Choice 2", "Choice 3"]
        )
        create_question_with_choices(
            question_text="Past question with choices 2.",
            days=-5,
            choices=["Choice 1", "Choice 2", "Choice 3"]
        )
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['latest_question_list'], [
            '<Question: Past question with choices 2.>',
            '<Question: Past question with choices 1.>'
            ]
        )


class QuestionDetailViewTests(TestCase):
    def test_past_question_without_choices(self):
        """
        The detail view of a question without choices with a pub_date
        in the past returns a 404 not found.
        """
        past_question_wo_choices = create_question(
            question_text="Past question without choices.",
            days=-30
        )
        url = reverse('polls:detail', args=(past_question_wo_choices.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question_with_choices(self):
        """
        The detail view of a question with choices with a pub_date
        in the past displays the question's text.
        """
        past_question_w_choices = create_question_with_choices(
            question_text="Past question with choices.",
            days=-30,
            choices=["Choice 1", "Choice 2", "Choice 3"]
        )
        url = reverse('polls:detail', args=(past_question_w_choices.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, past_question_w_choices.question_text)
        for choice in past_question_w_choices.choice_set.all():
            self.assertContains(response, choice)

    def test_future_question_without_choices(self):
        """
        The detail view of a question without choices with a pub_date
        in the future returns a 404 not found.
        """
        future_question_wo_choices = create_question(
            question_text="Future question without choices.",
            days=30
        )
        url = reverse('polls:detail', args=(future_question_wo_choices.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_future_question_with_choices(self):
        """
        The detail view of a question with choices with a pub_date
        in the future returns a 404 not found.
        """
        future_question_w_choices = create_question_with_choices(
            question_text="Future question with choices.",
            days=30,
            choices=["Choice 1", "Choice 2", "Choice 3"]
        )
        url = reverse('polls:detail', args=(future_question_w_choices.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class MakeChoiceTestCase(LiveServerTestCase):

  def test_vote(self):
    driver = Chrome(executable_path='C:\\WebDriver\\bin\\chromedriver')

    url_details = "http://localhost:8080/polls/{id}"
    url_results = "http://localhost:8080/polls/{id}/results"

    driver.get(url_results.format(id = 1))

    time.sleep(5)

    driver.get(url_details.format(id = 1))

    time.sleep(5)

    choice_form = driver.find_element_by_name("choiceForm")
    radio2 = choice_form.find_element_by_id("choice2")

    radio2.click()

    time.sleep(5)

    # driver.find_element_by_xpath('//input[@value="Vote"]').click()
    #
    # WebDriverWait(driver, 2).until(
    #     lambda waiter: waiter.find_element_by_tag_name('body')
    # )
    #
    # time.sleep(5)

    driver.quit()
