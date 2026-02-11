from django.http import JsonResponse
from core.models import User


def check_whatsapp_number(request):
    number = (request.GET.get("number") or "").strip()
    if not number:
        return JsonResponse({"error": "WhatsApp number not provided"}, status=400)

    exists = User.objects.filter(whatsapp_number=number).exists()
    return JsonResponse({"exists": exists, "number": number})
