from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.views.generic.edit import FormView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.shortcuts import get_object_or_404, render, redirect
from .models import Riddle, Option
from django.http import HttpResponseRedirect
from django.views.generic.base import View
from django.contrib.auth import logout
from django.contrib.auth.forms import PasswordChangeForm
from.models import Message
from datetime import datetime
from django.http import JsonResponse
import json
import numpy
from django import forms
from django.utils.translation import gettext, gettext_lazy as _





def index(request):
    message = None
    if "message" in request.GET:
        message = request.GET["message"]

    return render(
        request,
        "index.html",
        {
            "latest_riddles":
                Riddle.objects.order_by('-pub_date')[:10],
            "message": message
        }
    )

def detail(request, riddle_id):
    error_message = None
    if "error_message" in request.GET:
        error_message = request.GET["error_message"]
    # формируем список ответов
    ordered_option_set = \
        list(Option.objects.filter(riddle_id=riddle_id))
    # формируем случайный порядок номеров ответов
    option_iter = \
        numpy.random.permutation(len(ordered_option_set))
    # формируем новый список, в который выписываем ответы
    # в сформированном случайном порядке
    option_set = []
    for num in option_iter:
        option_set.append(ordered_option_set[num])
    return render(
        request,
        "answer.html",
        {
            # передаем список ответов в случайном порядке
            "option_set": option_set,

            "riddle": get_object_or_404(
                Riddle, pk=riddle_id),
            "error_message": error_message,
            "latest_messages":
                Message.objects
                    .filter(chat_id=riddle_id)
                    .order_by('-pub_date')[:5],
            # кол-во оценок, выставленных пользователем

        }
    )


def answer(request, riddle_id):
    riddle = get_object_or_404(Riddle, pk=riddle_id)
    try:
        option = riddle.option_set.get(pk=request.POST['option'])
    except (KeyError, Option.DoesNotExist):
        return redirect(
            '/AppRiddles/' + str(riddle_id) +
            '?error_message=Option does not exist',
        )
    else:
        if option.correct:
            return redirect(
                "/AppRiddles/?message=Nice! Choose another one!")
        else:
            return redirect(
                '/AppRiddles/'+str(riddle_id)+
                '?error_message=Wrong Answer!',
            )

app_url = "/AppRiddles/"
def post(request, riddle_id):
    msg = Message()
    msg.author = request.user
    msg.chat = get_object_or_404(Riddle, pk=riddle_id)
    msg.message = request.POST['message']
    msg.pub_date = datetime.now()
    msg.save()
    return HttpResponseRedirect(app_url+str(riddle_id))

def msg_list(request, riddle_id):
    # выбираем список сообщений
    res = list(
            Message.objects
                # фильтруем по id загадки
                .filter(chat_id=riddle_id)
                # отбираем 5 самых свежих
                .order_by('-pub_date')[:5]
                # выбираем необходимые поля
                .values('author__username',
                        'pub_date',
                        'message'
                )
            )
    for r in res:
        r['pub_date'] = \
            r['pub_date'].strftime(
                '%d.%m.%Y %H:%M:%S'
            )
    return JsonResponse(json.dumps(res), safe=False)

def admin(request):
    message = None
    if "message" in request.GET:
        message = request.GET["message"]
    # создание HTML-страницы по шаблону admin.html
    # с заданными параметрами latest_riddles и message
    return render(
        request,
        "admin.html",
        {
            "latest_riddles":
                Riddle.objects.order_by('-pub_date')[:5],
            "message": message,
        }
    )

def post_riddle(request):
    # защита от добавления загадок неадминистраторами
    author = request.user
    if not (author.is_authenticated and author.is_staff):
        return HttpResponseRedirect(app_url+"admin")
    # добавление загадки
    rid = Riddle()
    rid.riddle_text = request.POST['text']
    rid.pub_date = datetime.now()
    rid.save()
    # добавление вариантов ответа
    i = 1    # нумерация вариантов на форме начинается с 1
    # количество вариантов неизвестно,
    # поэтому ожидаем возникновение исключения,
    # когда варианты кончатся
    try:
        while request.POST['option'+str(i)]:
            opt = Option()
            opt.riddle = rid
            opt.text = request.POST['option'+str(i)]
            opt.correct = (i == 1)
            opt.save()
            i += 1
    # это ожидаемое исключение,
    # при котором ничего делать не надо
    except:
        pass

    for i in User.objects.all():
        # проверка, что текущий пользователь подписан - указал e-mail
        if i.email != '':
            send_mail(
                # тема письма
                'New riddle',
                # текст письма
                'A new riddle was added on riddles portal:\n' +
                'http://localhost:8000/AppRidles/' + str(rid.id) + '.',
                # отправитель
                'pythonmakavchik@gmail.com',
                # список получателей из одного получателя
                [i.email],
                # отключаем замалчивание ошибок,
                # чтобы из видеть и исправлять
                False
            )

    return HttpResponseRedirect(app_url+str(rid.id))


class RegisterFormView(FormView):
    # будем строить на основе
    # встроенной в django формы регистрации
    form_class = UserCreationForm
    # Ссылка, на которую будет перенаправляться пользователь
    # в случае успешной регистрации.
    # В данном случае указана ссылка на
    # страницу входа для зарегистрированных пользователей.
    success_url = app_url + "login/"
    # Шаблон, который будет использоваться
    # при отображении представления.
    template_name = "reg/register.html"
    def form_valid(self, form):
        # Создаём пользователя,
        # если данные в форму были введены корректно.
        form.save()
        # Вызываем метод базового класса
        return super(RegisterFormView, self).form_valid(form)


class LoginFormView(FormView):
    # будем строить на основе
    # встроенной в django формы входа
    form_class = AuthenticationForm
    # Аналогично регистрации,
    # только используем шаблон аутентификации.
    template_name = "reg/login.html"
    # В случае успеха перенаправим на главную.
    success_url = app_url
    def form_valid(self, form):
        # Получаем объект пользователя
        # на основе введённых в форму данных.
        self.user = form.get_user()
        # Выполняем аутентификацию пользователя.
        login(self.request, self.user)
        return super(LoginFormView, self).form_valid(form)

class LogoutView(View):
    def get(self, request):
        # Выполняем выход для пользователя,
        # запросившего данное представление.
        logout(request)
        # После чего перенаправляем пользователя на
        # главную страницу.
        return HttpResponseRedirect(app_url)

class PasswordChangeView(FormView):
    # будем строить на основе
    # встроенной в django формы смены пароля
    form_class = PasswordChangeForm
    template_name = 'reg/password_change_form.html'
    # после смены пароля нужно снова входить
    success_url = app_url + 'login/'
    def get_form_kwargs(self):
        kwargs = super(PasswordChangeView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
        return kwargs
    def form_valid(self, form):
        form.save()
        return super(PasswordChangeView, self).form_valid(form)


class SubscribeForm(forms.Form):
    # поле для ввода e-mail
    email = forms.EmailField(
        label=_("E-mail"),
        required=True,
    )

    # конструктор для запоминания пользователя,
    # которому задается e-mail
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    # сохранение e-mail
    def save(self, commit=True):
        self.user.email = self.cleaned_data["email"]
        if commit:
            self.user.save()
        return self.user


# класс, описывающий взаимодействие логики
# со страницами веб-приложения
class SubscribeView(FormView):
    # используем класс с логикой
    form_class = SubscribeForm
    # используем собственный шаблон
    template_name = 'subscribe.html'
    # после подписки возвращаем на главную станицу
    success_url = app_url

    # передача пользователя для конструктора класса с логикой
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    # вызов логики сохранения введенных данных
    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.success_url)

def unsubscribe(request):
    request.user.email = ''
    request.user.save()
    return HttpResponseRedirect(app_url)
