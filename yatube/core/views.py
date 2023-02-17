from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


def page_not_found(request, exception):
    return render(request, 'core/404.html', {'path': request.path}, status=404)


@csrf_exempt
def csrf_failure(request, exception):
    c = {}
    return render(request, 'core/403csrf.html', c, status=403)
