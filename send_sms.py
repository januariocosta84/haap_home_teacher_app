from twilio.rest import Client

# Your Account SID and Auth Token from console.twilio.com
account_sid = ""
auth_token  = ""


client = Client(account_sid, auth_token)

message = client.messages.create(
    from_='whatsapp:+14155238886',   # Twilio Sandbox WhatsApp number
    body='Hello from WhatsApp via Twilio!',
    to='whatsapp:+67077121173'       # recipient WhatsApp number
)

print(message.sid)