from .models import HomePage

def home_data(request):
    return {
        "home_data": HomePage.objects.first()
    }