import requests

FONNTE_TOKEN = "fU3iADWKve58kdnaFNzh"
URL = "https://api.fonnte.com/send"

def send_whatsapp_message(target, message):
    headers = {
        "Authorization": FONNTE_TOKEN
    }

    data = {
        "target": target,      # phone number (e.g. 628123456789)
        "message": message,    # your message text
        "countryCode": "+670"    # optional (Indonesia default)
    }

    response = requests.post(URL, headers=headers, data=data)

    return response.json()


# Example usage
if __name__ == "__main__":
    result = send_whatsapp_message(
        target="77121173",
        message="Hello from Python + Fonnte 🚀"
    )

    print(result)