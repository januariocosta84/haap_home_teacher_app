# WhatsApp Report Generation System

## Overview
This system automatically generates and sends child activity reports to parents via WhatsApp using Twilio's WhatsApp Business API.

## Features
- 📊 Generates activity summaries for each child
- 📱 Sends reports via WhatsApp 
- 🎯 Includes achievement rates and activity themes
- 📅 Configurable report period (default: 30 days)
- 🔄 Can be scheduled via Django management command
- 🔐 Role-based access control
- 🧪 Dry-run mode for testing

## Setup Instructions

### 1. Install Twilio SDK
```bash
pip install twilio
```
Update requirements.txt:
```bash
echo "twilio==9.2.0" >> requirements.txt
```

### 2. Get Twilio Credentials
1. Go to https://www.twilio.com/
2. Sign up for a free account
3. Navigate to WhatsApp Settings in your Twilio Console
4. Set up a WhatsApp Business Account
5. Get your:
   - Account SID
   - Auth Token
   - WhatsApp Sender Number (format: `whatsapp:+1234567890`)

### 3. Configure .env File
Add these variables to `/var/www/haap_app/.env`:
```env
# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+1234567890
```

### 4. Update Settings (if needed)
The system checks for these environment variables automatically.

## Usage

### Option 1: Management Command (Scheduled Reports)
Run reports for all parents:
```bash
python manage.py send_whatsapp_reports
```

Send reports for last 7 days:
```bash
python manage.py send_whatsapp_reports --days 7
```

Send report for specific parent:
```bash
python manage.py send_whatsapp_reports --parent-id <parent-uuid>
```

Send report for specific child:
```bash
python manage.py send_whatsapp_reports --child-id <child-uuid>
```

Dry-run (preview without sending):
```bash
python manage.py send_whatsapp_reports --dry-run
```

### Option 2: API Endpoints

#### Send Report for Single Child
**POST** `/api/send-child-report/{child_id}/`

Request body:
```json
{
  "days": 30
}
```

Response:
```json
{
  "success": true,
  "message": "Report sent successfully",
  "report": {
    "child_name": "João",
    "total_activities": 15,
    "achieved_activities": 12,
    "achievement_rate": 80.0,
    ...
  },
  "recipient": "+67012345678"
}
```

#### Send Reports for All Children  
**POST** `/api/send-all-reports/`

Request body:
```json
{
  "days": 30
}
```

Response:
```json
{
  "success": 5,
  "failed": 0,
  "message": "Sent 5 reports, failed: 0"
}
```

### Option 3: Python Script/View
```python
from core.services.report_generator import get_report_generator
from core.services.whatsapp_service import get_whatsapp_service
from core.models import Child

# Get a child
child = Child.objects.get(id='...')

# Generate report
generator = get_report_generator(days=30)
report = generator.generate_child_report(child)
message = generator.format_whatsapp_message(report)

# Send via WhatsApp
whatsapp = get_whatsapp_service()
success = whatsapp.send_message(child.parent.whatsapp_number, message)
```

## Scheduling (Optional)

### Using APScheduler or Celery for Periodic Tasks
If you want reports sent automatically on a schedule (e.g., monthly):

#### With Django Cron:
Install django-crontab:
```bash
pip install django-crontab
```

Add to `settings.py`:
```python
CRONJOBS = [
    # Send reports every last day of the month at 8 AM
    ('0 8 L * *', 'core.cron.send_monthly_reports'),
]
```

Create `core/cron.py`:
```python
from django.core.management import call_command

def send_monthly_reports():
    call_command('send_whatsapp_reports', '--days', '30')
```

#### With Celery:
Create `core/tasks.py`:
```python
from celery import shared_task
from core.services.report_generator import get_report_generator
from core.services.whatsapp_service import get_whatsapp_service
from core.models import Child, User

@shared_task
def send_monthly_reports():
    generator = get_report_generator(days=30)
    whatsapp = get_whatsapp_service()
    
    parents = User.objects.filter(role='parent', children__isnull=False).distinct()
    
    for parent in parents:
        for child in parent.children.all():
            report = generator.generate_child_report(child)
            message = generator.format_whatsapp_message(report)
            whatsapp.send_message(parent.whatsapp_number, message)
```

Then schedule in Celery Beat configuration.

## Report Format

Reports include:
- 📊 **Statistics**: Total Activities, Achieved Activities, Achievement Rate
- 🎯 **Top Themes**: Most worked on activity categories
- 📝 **Recent Activities**: Last 3 activities completed
- ✅ **All in Tetum**: Messages are formatted in Tetum language for local context

Example message:
```
*Relaváu Atividade Estudante* 📚

Olá Maria Dos Santos,

Nia Atualizasaun ba João (Grupo A: Tinan 3-4)

*Período:* Últimos 30 diás (05 April 2026)

📊 *Resulta Prinsipál:*
• Total Atividade: 15
• Atinji Rezultadu: 12
• Taxa Atinji: 80.0%

🎯 *Tópiku Prinsipál:*
• Motor Skills: 8 atividade
• Language: 5 atividade

📝 *Atividade Resente:*
• Puzzle Activity - Resolved puzzle successfully
• Drawing Activity - Created shapes

Para informasaun detalhádu, haree iha portal HAAP.

Obrigádu! 🌟
```

## Error Handling

- If Twilio credentials are not configured, system logs warnings and provides helpful messages
- Failed sending attempts are logged and reported
- Reports can be generated even if WhatsApp is not configured (for testing/dry-run)

## Testing

### 1. Dry-run Test
```bash
python manage.py send_whatsapp_reports --dry-run
```

### 2. Test Single Child
```bash
python manage.py send_whatsapp_reports --child-id <uuid> --days 30
```

### 3. Check Logs
```bash
tail -f logs/django.log | grep WhatsApp
```

## Troubleshooting

### Issue: "WhatsApp service not configured"
- Solution: Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM to .env
- Check: `python manage.py shell` → `from core.services.whatsapp_service import get_whatsapp_service; ws = get_whatsapp_service(); print(ws.enabled)`

### Issue: "Failed to send WhatsApp message"
- Check Twilio credentials are correct
- Verify recipient phone number is in correct format: `+countrycode123456789`
- Check Twilio console for API errors
- Ensure Twilio account has WhatsApp capability enabled

### Issue: Reports show 0% achievement
- This is fixed if you ran the previous fix for activity_result filtering
- Activity results should NOT be 'Tentadu' or empty
- Check data: `ActivityResult.objects.filter(student__id='<child-id>').values_list('activity_result', flat=True).distinct()`

## Files Created

```
core/
├── services/
│   ├── whatsapp_service.py        # WhatsApp sending service
│   └── report_generator.py         # Report generation logic
├── management/
│   └── commands/
│       └── send_whatsapp_reports.py  # Management command
├── api_reports.py                 # API endpoints for reports
└── [existing files]
```

## Security Notes

- API endpoints check user permissions (parents can only access their child's reports)
- MOE admins can send reports for all parents
- Phone numbers are stored securely in User model
- Credentials are managed via environment variables, never hardcoded
