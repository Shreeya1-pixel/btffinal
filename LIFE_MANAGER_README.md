# Life Manager - Personal AI Assistant

## Overview

Life Manager transforms Neuroverse into a personal operating system that manages your daily communications and tasks. It supports WhatsApp, Gmail, and Instagram with intelligent contact resolution and zero-LLM routing for simple actions.

## Architecture

### Core Components

1. **Contact Manager** (`backend/services/contact_manager.py`)
   - Maps contact names to communication channels
   - Supports aliases (e.g., "mom", "mother", "mama")
   - Resolves names to email, phone, or Instagram handles
   - Extensible for integration with Google Contacts API

2. **Life Manager Tools** (`backend/tools/life_manager_tools.py`)
   - Gmail: Draft and send emails
   - WhatsApp: Generate deep links for messaging
   - Instagram: Generate conversation links
   - Scheduling: Create calendar events
   - Tasks: Create to-do items
   - Contacts: Add/update contact information

3. **Keyword-Based Routing** (`backend/agents/`)
   - **Orchestrator**: Detects "email", "whatsapp", "instagram" keywords
   - **Tool Executor**: Parses recipient names and message content
   - **Zero-LLM Execution**: Simple commands bypass API calls entirely

## Features

### 🔹 Contact Resolution

Use natural names instead of technical identifiers:

```
✓ "send hi to mom on whatsapp"              → +1234567890
✓ "email boss about the meeting"            → boss@company.com
✓ "dm dad on instagram saying hello"        → @dad_instagram
```

### 🔹 Draft vs. Send Workflow

**Direct Send** (keyword-based, no API):
```
send hi to mom on whatsapp
send hello to boss on gmail
dm dad on instagram saying how are you
```

**Draft First** (uses LLM for content generation):
```
draft an email to mom about the party
draft a whatsapp message to boss with meeting notes
```

### 🔹 Supported Queries

#### WhatsApp
```
send hi to mom on whatsapp
whatsapp mom saying I'll be late
message dad on wa
```

#### Gmail
```
send email to boss about the report
gmail mom a quick hello
email dad saying I miss you
```

#### Instagram
```
dm mom on instagram
send instagram message to dad
instagram boss asking about the project
```

## Usage Examples

### Simple Messaging (No API Key Needed)

```bash
# WhatsApp
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "send hi to mom on whatsapp"}'

Response:
{
  "status": "link_generated",
  "whatsapp_url": "https://wa.me/1234567890?text=hi",
  "phone_number": "+1234567890",
  "to_name": "mom"
}

# Gmail
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "send hello to boss on gmail"}'

Response:
{
  "status": "link_generated",
  "mailto_link": "mailto:boss@company.com?subject=Quick%20message&body=hello",
  "to": "boss@company.com",
  "to_name": "boss"
}

# Instagram
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "dm dad on instagram saying how are you"}'

Response:
{
  "status": "link_generated",
  "instagram_url": "https://www.instagram.com/direct/t/dad_instagram/",
  "instagram_handle": "@dad_instagram",
  "to_name": "dad",
  "message": "how are you"
}
```

### Contact Management

```bash
# Add a new contact
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "add contact john with email john@example.com and phone +1234567899"
  }'

# Now you can use the contact
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "send hi to john on whatsapp"}'
```

## Integration Points

### Production-Ready Integrations

#### Gmail API (Recommended)
```python
# In backend/tools/life_manager_tools.py -> send_gmail()

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# OAuth2 flow
creds = Credentials.from_authorized_user_info(token_data, SCOPES)
service = build('gmail', 'v1', credentials=creds)

# Send email
message = create_message('me', to, subject, body)
service.users().messages().send(userId='me', body=message).execute()
```

#### Instagram Graph API
```python
# In backend/tools/life_manager_tools.py -> send_instagram()

from facebook_business.api import FacebookAdsApi

FacebookAdsApi.init(access_token=token)
# Use Instagram Messaging API for business accounts
# Or Instagram Basic Display API for personal accounts
```

#### Google Calendar API
```python
# In backend/tools/life_manager_tools.py -> schedule_event()

service = build('calendar', 'v3', credentials=creds)

event = {
    'summary': title,
    'start': {'dateTime': start_time},
    'end': {'dateTime': end_time},
    'attendees': [{'email': email} for email in attendees]
}

service.events().insert(calendarId='primary', body=event).execute()
```

## Code Quality Standards

### Clean Code Principles

1. **Single Responsibility**: Each function has one clear purpose
2. **Dependency Injection**: Contact manager is injected, not hardcoded
3. **Error Handling**: Comprehensive try-catch with structured logging
4. **Type Hints**: All functions use Python type annotations
5. **Documentation**: Docstrings follow Google style guide
6. **Logging**: Structured logging with context (via structlog)
7. **Testing Ready**: Pure functions enable easy unit testing

### Example: Contact Resolution
```python
# Clean, testable, documented
async def send_whatsapp(to: str, message: str) -> str:
    """
    Generate WhatsApp deep link to send message.
    
    Opens WhatsApp (web or mobile) with pre-filled message.
    
    Args:
        to: Recipient name or phone number
        message: Message content
        
    Returns:
        JSON string with WhatsApp link
    """
    # Resolve contact name to phone number
    resolved_phone = contact_manager.get_phone(to) or to
    
    # Clean phone number (remove non-digits)
    clean_phone = "".join(filter(str.isdigit, resolved_phone))
    
    # Create WhatsApp deep link
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_message}"
    
    # Structured response
    result = {
        "status": "link_generated",
        "whatsapp_url": whatsapp_url,
        "phone_number": resolved_phone,
        "to_name": to,
        "message": "Opening WhatsApp with your message..."
    }
    
    logger.info("whatsapp_link_generated", to=to, resolved=resolved_phone)
    return json.dumps(result)
```

## Performance

### Zero-LLM Execution

Simple messaging commands execute without any API calls:

- **Orchestrator**: Keyword detection (< 1ms)
- **Tool Executor**: Pattern matching (< 1ms)
- **Contact Resolution**: Dictionary lookup (< 1ms)
- **Total**: ~2ms end-to-end

**Example benchmark:**
```json
{
  "query": "send hi to mom on whatsapp",
  "duration_ms": 1.85,
  "keyword_routing": true,
  "direct_execution": true,
  "llm_calls": 0
}
```

## Security Considerations

### Contact Data
- Currently in-memory (development)
- **Production**: Encrypt contact data at rest
- **Production**: Use OAuth2 for API integrations
- **Production**: Implement user authentication

### Message Privacy
- Messages never logged in production
- Deep links contain message content (HTTPS only)
- Consider end-to-end encryption for stored drafts

## Future Enhancements

### Planned Features
1. **Voice Notes**: Transcribe and send voice messages
2. **Smart Scheduling**: AI-powered meeting time suggestions
3. **Batch Operations**: "Send same message to mom and dad"
4. **Templates**: Pre-defined message templates
5. **Analytics**: Message frequency, response times

### API Integrations
- [ ] Google Workspace (Gmail, Calendar, Contacts)
- [ ] Microsoft 365 (Outlook, Teams)
- [ ] Slack
- [ ] Twitter/X DMs
- [ ] Telegram
- [ ] WhatsApp Business API

## Testing

### Unit Tests
```python
# tests/test_contact_manager.py
def test_resolve_contact():
    manager = ContactManager()
    contact = manager.resolve_contact("mom")
    assert contact.email == "mom@example.com"
    assert contact.phone == "+1234567890"

def test_alias_resolution():
    manager = ContactManager()
    contact = manager.resolve_contact("mother")  # alias
    assert contact.name == "Mom"
```

### Integration Tests
```python
# tests/test_life_manager_tools.py
@pytest.mark.asyncio
async def test_send_whatsapp():
    result_json = await send_whatsapp(to="mom", message="hi")
    result = json.loads(result_json)
    
    assert result["status"] == "link_generated"
    assert "wa.me" in result["whatsapp_url"]
    assert result["to_name"] == "mom"
```

## Deployment

### Environment Variables
```env
# Required
OPENAI_API_KEY=sk-...  # Only for draft/LLM features

# Optional (for production integrations)
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
INSTAGRAM_ACCESS_TOKEN=xxx
```

### Docker Deployment
```bash
# Build and run
docker-compose up --build -d

# Check logs
docker-compose logs -f backend

# Health check
curl http://localhost:8000/api/chat \
  -d '{"query": "send hi to mom on whatsapp"}'
```

## Contributing

### Adding a New Communication Channel

1. **Add to Contact Manager**
```python
class Contact:
    def __init__(self, ..., slack: Optional[str] = None):
        self.slack = slack
```

2. **Create Tool Functions**
```python
async def send_slack(to: str, message: str) -> str:
    """Send Slack message."""
    pass
```

3. **Register Tools**
```python
tool_registry.register(ToolDefinition(
    name="send_slack",
    description="Send a Slack message",
    parameters=[...],
    function=send_slack,
    module="life-manager"
))
```

4. **Update Keyword Detection**
```python
# In orchestrator.py
life_manager_keywords = [..., "slack", "send slack"]

# In tool_executor.py
if "slack" in query_lower:
    return ("send_slack", {"to": recipient, "message": message})
```

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- GitHub Issues: [Repository Issues]
- Documentation: [Full Docs]
- Email: support@neuroverse.ai

