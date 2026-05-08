

from django.http import JsonResponse

from core.services.whatsapp import WhatsAppService


def send_whatsapp(request):
    phone = "67077121173"
    message = "Hello from Django WhatsApp"

    whatsapp = WhatsAppService()
    
    result = whatsapp.send_message(
        phone=phone,
        message=message
    )

    return JsonResponse({
        "success": result
    })