from django.shortcuts import get_object_or_404
from django.views.generic import FormView

from .forms import ObserveForm
from accounts.models import StripChatUser
from .services.parsing_service import run_in_thread


class MainPageView(FormView):
    form_class = ObserveForm
    template_name = "main.html"

    def post(self, request, *args, **kwargs):
        login_user = request.POST.get("user")
        search_username = request.POST.get("username")
        strip_chat_user = get_object_or_404(StripChatUser, id=login_user)
        run_in_thread(strip_chat_user, search_username)
        return self.get(request, *args, **kwargs)
