from django.core.paginator import Paginator


def pagination(request, post_list):
    """Разбивает список постов post_list на страницы по 10 штук"""
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
