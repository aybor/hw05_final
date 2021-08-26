from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """Статическая страница об авторе."""
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """Статическая страница об использованнх технологиях."""
    template_name = 'about/tech.html'
