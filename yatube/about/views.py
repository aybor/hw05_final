from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """Статическая страница об авторе."""
    template_name = 'about/author.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)


class AboutTechView(TemplateView):
    """Статическая страница об использованнх технологиях."""
    template_name = 'about/tech.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)
