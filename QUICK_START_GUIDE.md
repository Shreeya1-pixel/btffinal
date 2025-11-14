# Life Manager - Quick Start Guide

## 🚀 Access the Application

**Frontend**: http://localhost:80

## 📝 Example Queries

### WhatsApp
```
✓ "send hi to mom on whatsapp"
✓ "whatsapp dad saying I'll be late"
✓ "message boss on wa"
```

### Gmail
```
✓ "send hello to boss on gmail"
✓ "email mom a quick message"
✓ "gmail dad saying miss you"
```

### Instagram
```
✓ "dm mom on instagram"
✓ "send instagram message to dad"
✓ "insta boss asking about project"
```

### Draft Mode (Uses AI)
```
✓ "draft an email to mom about the party"
✓ "draft a whatsapp message to boss"
```

## 👥 Default Contacts

| Name | Email | Phone | Instagram |
|------|-------|-------|-----------|
| Mom | mom@example.com | +1234567890 | @mom_instagram |
| Dad | dad@example.com | +1234567891 | @dad_instagram |
| Boss | boss@company.com | +1234567892 | @boss_instagram |

## 🎯 How It Works

### Simple Send (No API Key Needed)
```
You: "send hi to mom on whatsapp"
     ↓
AI detects: keyword "whatsapp" → routes to life-manager (< 1ms)
     ↓
AI parses: recipient="mom", message="hi", channel="whatsapp"
     ↓
Contact Manager: "mom" → +1234567890
     ↓
Result: WhatsApp link opens automatically
Total time: ~2ms, 0 API calls
```

### Draft Mode (Uses AI for Content)
```
You: "draft an email to mom"
     ↓
AI generates: subject and body using LLM
     ↓
Shows approval UI with "Send" button
     ↓
You approve → opens email client
Total time: ~800ms, 1 API call
```

## 🎨 User Interface

### Approval Workflow
When you draft a message, you'll see:
- ✅ **Approve & Send**: Opens app to send
- ✏️ **Edit**: Modify the message
- ❌ **Cancel**: Discard draft

### Message Display
```
You: send hi to mom on whatsapp
Bot: ✓ Opening WhatsApp to send message to mom...
     [WhatsApp opens in new tab]
```

## 🔧 Adding Your Own Contacts

### Via Chat
```
"add contact john with email john@example.com and phone +1234567899"
```

### Via Code
Edit: `backend/services/contact_manager.py`
```python
self._contacts = {
    "john": Contact(
        name="John",
        email="john@example.com",
        phone="+1234567899",
        instagram="@john_insta"
    ),
    # ... more contacts
}
```

## 🧪 Testing Without Frontend

### WhatsApp
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "send hi to mom on whatsapp"}'
```

### Gmail
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "send hello to boss on gmail"}'
```

### Instagram
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "dm dad on instagram saying how are you"}'
```

## 🎓 Tips & Tricks

### Natural Language
The system understands variations:
- "send", "message", "text", "dm"
- "to mom", "message mom", "mom on..."
- "saying hello", "hello", "'hello'"

### Contact Aliases
Works with aliases:
- "mom", "mother", "mama" → Same contact
- "dad", "father", "papa" → Same contact
- "boss", "manager", "supervisor" → Same contact

### Message Extraction
Supports multiple formats:
```
✓ send "hello world" to mom
✓ send hello to mom
✓ message mom saying hello
✓ tell mom hello on whatsapp
```

## ⚡ Performance

### Zero-LLM Mode (Direct Send)
- Execution: < 2ms
- API Calls: 0
- Cost: $0.00
- Works without OpenAI API key

### LLM-Assisted Mode (Draft)
- Execution: ~800ms
- API Calls: 1 (gpt-4o)
- Cost: ~$0.001
- Requires OpenAI API key

## 🐛 Troubleshooting

### "Network Error"
```bash
# Check if backend is running
docker-compose ps

# Restart if needed
docker-compose restart backend
```

### "Contact not found"
Add the contact first:
```
"add contact john with email john@example.com"
```

### Links not opening
- Check browser pop-up blocker settings
- Ensure you're logged into WhatsApp/Instagram

## 📚 Documentation

- **Full Documentation**: See LIFE_MANAGER_README.md
- **Implementation Details**: See IMPLEMENTATION_SUMMARY.md
- **Architecture**: See ARCHITECTURE_DIAGRAM.md

## 🎉 You're Ready!

Try your first command:
```
"send hi to mom on whatsapp"
```

The system will:
1. Detect "whatsapp" keyword
2. Resolve "mom" to phone number
3. Open WhatsApp with your message
4. All in under 2ms!

**Enjoy your personal AI assistant!** 🤖✨

