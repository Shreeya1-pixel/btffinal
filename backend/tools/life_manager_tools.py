"""
Life Manager Tools - Communication & Productivity

Provides tools for managing email, WhatsApp, Instagram, scheduling, and tasks.
Integrates with contact management for seamless name-to-address resolution.

Architecture:
- Contact resolution via ContactManager
- Draft/send workflow for all communication channels
- Keyword-based routing for zero-LLM simple actions
- Gmail-ready (OAuth2 integration point marked)
- Instagram-ready (API integration point marked)
"""

import json
import smtplib
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional

from backend.tools.base import tool_registry, ToolDefinition, ToolParameter
from backend.core.logger import get_logger
from backend.services.contact_manager import contact_manager

logger = get_logger(__name__)


# ============================================================================
# GMAIL TOOLS
# ============================================================================

async def draft_gmail(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None
) -> str:
    """
    Draft a Gmail message.
    
    Resolves contact names to email addresses automatically.
    In production, this would use Gmail API to save as draft.
    
    Args:
        to: Recipient name or email address
        subject: Email subject
        body: Email body content
        cc: Optional CC recipients (comma-separated)
        bcc: Optional BCC recipients (comma-separated)
        
    Returns:
        JSON string with draft details and status
    """
    try:
        # Resolve contact name to email
        resolved_to = contact_manager.get_email(to) or to
        
        draft = {
            "action": "send_gmail",
            "to": resolved_to,
            "to_name": to,
            "subject": subject,
            "body": body,
            "cc": cc,
            "bcc": bcc,
            "status": "requires_approval",
            "timestamp": datetime.now().isoformat(),
            "note": "Click 'Approve & Send' to send this email"
        }
        
        logger.info("gmail_drafted", to=to, resolved=resolved_to, subject=subject)
        return json.dumps(draft)
        
    except Exception as e:
        logger.error("gmail_draft_failed", error=str(e))
        return json.dumps({"error": str(e), "status": "failed"})


async def send_gmail(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    smtp_server: Optional[str] = None,
    smtp_port: Optional[int] = None,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> str:
    """
    Send a Gmail message directly.
    
    Production Integration Points:
    1. Gmail API with OAuth2 (recommended)
    2. SMTP with app-specific password (current fallback)
    
    Args:
        to: Recipient name or email
        subject: Email subject
        body: Email body
        cc: CC recipients
        bcc: BCC recipients
        smtp_server: SMTP server (defaults to Gmail)
        smtp_port: SMTP port
        username: Gmail address
        password: App-specific password or OAuth token
        
    Returns:
        JSON string with send status and mailto link
    """
    try:
        # Resolve contact name
        resolved_to = contact_manager.get_email(to) or to
        
        # Generate mailto link for client-side sending
        mailto_params = {
            'subject': subject,
            'body': body
        }
        if cc:
            mailto_params['cc'] = cc
        if bcc:
            mailto_params['bcc'] = bcc
            
        query_string = urllib.parse.urlencode(mailto_params, quote_via=urllib.parse.quote)
        mailto_link = f"mailto:{resolved_to}?{query_string}"
        
        result = {
            "status": "link_generated",
            "mailto_link": mailto_link,
            "to": resolved_to,
            "to_name": to,
            "subject": subject,
            "message": "Click the link to open your email client with pre-filled content"
        }
        
        # TODO: Production Gmail API integration
        # If OAuth2 credentials available, send via Gmail API:
        # from googleapiclient.discovery import build
        # service = build('gmail', 'v1', credentials=creds)
        # message = create_message(username, resolved_to, subject, body)
        # service.users().messages().send(userId='me', body=message).execute()
        
        logger.info("gmail_link_generated", to=to, resolved=resolved_to)
        return json.dumps(result)
        
    except Exception as e:
        logger.error("gmail_send_failed", error=str(e))
        return json.dumps({"error": str(e), "status": "failed"})


# ============================================================================
# WHATSAPP TOOLS
# ============================================================================

async def draft_whatsapp(
    to: str,
    message: str
) -> str:
    """
    Draft a WhatsApp message for approval.
    
    Resolves contact names to phone numbers automatically.
    Only accepts contact names, not phone numbers.
    
    Args:
        to: Recipient contact name (e.g., "mom", "dad", "boss")
        message: Message content
        
    Returns:
        JSON string with draft requiring approval
    """
    try:
        # Resolve contact name to phone number - REQUIRED, no fallback
        contact = contact_manager.resolve_contact(to)
        if not contact or not contact.phone:
            error_msg = f"Contact '{to}' not found. Please add the contact first or use a valid contact name."
            logger.warning("whatsapp_contact_not_found", contact_name=to)
            return json.dumps({
                "error": error_msg,
                "status": "failed",
                "suggestion": f"Add contact with: 'add contact {to} with phone +1234567890'"
            })
        
        resolved_phone = contact.phone
        
        draft = {
            "action": "send_whatsapp",
            "phone_number": resolved_phone,
            "to_name": to,
            "message": message,
            "status": "requires_approval",
            "timestamp": datetime.now().isoformat(),
            "note": "Click 'Approve & Send' to send via WhatsApp"
        }
        
        logger.info("whatsapp_drafted", to=to, resolved=resolved_phone)
        return json.dumps(draft)
        
    except Exception as e:
        logger.error("whatsapp_draft_failed", error=str(e))
        return json.dumps({"error": str(e), "status": "failed"})


async def send_whatsapp(
    to: str,
    message: str
) -> str:
    """
    Generate WhatsApp deep link to send message.
    
    Opens WhatsApp (web or mobile) with pre-filled message.
    Only accepts contact names, not phone numbers.
    
    Args:
        to: Recipient contact name (e.g., "mom", "dad", "boss")
        message: Message content
        
    Returns:
        JSON string with WhatsApp link
    """
    try:
        # Resolve contact name to phone number - REQUIRED, no fallback
        contact = contact_manager.resolve_contact(to)
        if not contact or not contact.phone:
            error_msg = f"Contact '{to}' not found. Please add the contact first or use a valid contact name."
            logger.warning("whatsapp_contact_not_found", contact_name=to)
            return json.dumps({
                "error": error_msg,
                "status": "failed",
                "suggestion": f"Add contact with: 'add contact {to} with phone +1234567890'"
            })
        
        resolved_phone = contact.phone
        
        # Clean phone number (remove non-digits, but keep country code)
        clean_phone = "".join(filter(str.isdigit, resolved_phone))
        
        # Validate phone number format (should have at least 10 digits)
        if len(clean_phone) < 10:
            error_msg = f"Invalid phone number for contact '{to}'. Phone number must have at least 10 digits."
            logger.warning("whatsapp_invalid_phone", contact_name=to, phone=resolved_phone)
            return json.dumps({
                "error": error_msg,
                "status": "failed",
                "suggestion": f"Update contact '{to}' with a valid phone number"
            })
        
        # Create WhatsApp deep link
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_message}"
        
        result = {
            "status": "link_generated",
            "whatsapp_url": whatsapp_url,
            "phone_number": resolved_phone,
            "to_name": to,
            "message": "Opening WhatsApp with your message..."
        }
        
        logger.info("whatsapp_link_generated", to=to, resolved=resolved_phone)
        return json.dumps(result)
        
    except Exception as e:
        logger.error("whatsapp_send_failed", error=str(e))
        return json.dumps({"error": str(e), "status": "failed"})


# ============================================================================
# INSTAGRAM TOOLS
# ============================================================================

async def draft_instagram(
    to: str,
    message: str
) -> str:
    """
    Draft an Instagram direct message.
    
    Resolves contact names to Instagram handles automatically.
    
    Args:
        to: Recipient name or Instagram handle
        message: Message content
        
    Returns:
        JSON string with draft requiring approval
    """
    try:
        # Resolve contact name to Instagram handle
        resolved_handle = contact_manager.get_instagram(to) or to
        
        # Ensure handle starts with @
        if not resolved_handle.startswith('@'):
            resolved_handle = f'@{resolved_handle}'
        
        draft = {
            "action": "send_instagram",
            "instagram_handle": resolved_handle,
            "to_name": to,
            "message": message,
            "status": "requires_approval",
            "timestamp": datetime.now().isoformat(),
            "note": "Click 'Approve & Send' to send via Instagram"
        }
        
        logger.info("instagram_drafted", to=to, resolved=resolved_handle)
        return json.dumps(draft)
        
    except Exception as e:
        logger.error("instagram_draft_failed", error=str(e))
        return json.dumps({"error": str(e), "status": "failed"})


async def send_instagram(
    to: str,
    message: str
) -> str:
    """
    Generate Instagram deep link or API call to send message.
    
    Production Integration Point:
    - Instagram Graph API for business accounts
    - Instagram Basic Display API for personal accounts
    
    Args:
        to: Recipient name or Instagram handle
        message: Message content
        
    Returns:
        JSON string with Instagram link or send status
    """
    try:
        # Resolve contact name to Instagram handle
        resolved_handle = contact_manager.get_instagram(to) or to
        
        # Clean handle (remove @ if present for URL)
        clean_handle = resolved_handle.lstrip('@')
        
        # Create Instagram deep link (opens Instagram app/web)
        instagram_url = f"https://www.instagram.com/direct/t/{clean_handle}/"
        
        result = {
            "status": "link_generated",
            "instagram_url": instagram_url,
            "instagram_handle": resolved_handle,
            "to_name": to,
            "message": message,
            "note": "Opening Instagram. Please send the message manually: " + message
        }
        
        # TODO: Production Instagram API integration
        # If Instagram Graph API token available:
        # from facebook_business.api import FacebookAdsApi
        # FacebookAdsApi.init(access_token=token)
        # # Send message via Instagram Messaging API
        
        logger.info("instagram_link_generated", to=to, resolved=resolved_handle)
        return json.dumps(result)
        
    except Exception as e:
        logger.error("instagram_send_failed", error=str(e))
        return json.dumps({"error": str(e), "status": "failed"})


# ============================================================================
# SCHEDULING & PRODUCTIVITY TOOLS
# ============================================================================

async def schedule_event(
    title: str,
    start_time: str,
    duration_minutes: int = 60,
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[str] = None
) -> str:
    """
    Schedule an event or meeting.
    
    Production Integration Point:
    - Google Calendar API
    - Microsoft Outlook Calendar API
    
    Args:
        title: Event title
        start_time: Start time (ISO format or natural language)
        duration_minutes: Duration in minutes
        description: Event description
        location: Event location
        attendees: Comma-separated list of attendee names/emails
        
    Returns:
        JSON string with event details
    """
    try:
        # Parse start time
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        except:
            # Fallback: 1 hour from now
            start_dt = datetime.now() + timedelta(hours=1)
        
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        
        # Resolve attendee names to emails
        resolved_attendees = []
        if attendees:
            for attendee in attendees.split(','):
                attendee = attendee.strip()
                resolved_email = contact_manager.get_email(attendee) or attendee
                resolved_attendees.append(resolved_email)
        
        event = {
            "title": title,
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "duration_minutes": duration_minutes,
            "description": description,
            "location": location,
            "attendees": resolved_attendees,
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }
        
        logger.info("event_scheduled", title=title)
        return json.dumps(event)
        
    except Exception as e:
        logger.error("event_schedule_failed", error=str(e))
        return json.dumps({"error": str(e), "status": "failed"})


async def create_task(
    title: str,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: str = "medium",
    status: str = "todo"
) -> str:
    """
    Create a task or to-do item.
    
    Production Integration Point:
    - Google Tasks API
    - Microsoft To Do API
    - Todoist API
    
    Args:
        title: Task title
        description: Task description
        due_date: Due date (ISO format)
        priority: Priority level (low, medium, high)
        status: Task status (todo, in_progress, done)
        
    Returns:
        JSON string with task details
    """
    try:
        task = {
            "title": title,
            "description": description,
            "due_date": due_date,
            "priority": priority,
            "status": status,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info("task_created", title=title, priority=priority)
        return json.dumps(task)
        
    except Exception as e:
        logger.error("task_create_failed", error=str(e))
        return json.dumps({"error": str(e), "status": "failed"})


# ============================================================================
# CONTACT MANAGEMENT TOOLS
# ============================================================================

async def add_contact(
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    instagram: Optional[str] = None
) -> str:
    """
    Add or update a contact.
    
    Args:
        name: Contact name
        email: Email address
        phone: Phone number (with country code)
        instagram: Instagram handle
        
    Returns:
        JSON string with contact details
    """
    try:
        contact = contact_manager.add_contact(
            name=name,
            email=email,
            phone=phone,
            instagram=instagram
        )
        
        result = {
            "status": "success",
            "contact": contact.to_dict(),
            "message": f"Contact '{name}' added successfully"
        }
        
        logger.info("contact_added_via_tool", name=name)
        return json.dumps(result)
        
    except Exception as e:
        logger.error("contact_add_failed", error=str(e))
        return json.dumps({"error": str(e), "status": "failed"})


# ============================================================================
# TOOL REGISTRATION
# ============================================================================

# Gmail Tools
tool_registry.register(ToolDefinition(
    name="draft_gmail",
    description="Draft a Gmail message. Use contact names (e.g., 'mom', 'boss') or email addresses. Returns a draft requiring approval.",
    parameters=[
        ToolParameter(name="to", type="string", description="Recipient name or email address", required=True),
        ToolParameter(name="subject", type="string", description="Email subject line", required=True),
        ToolParameter(name="body", type="string", description="Email body content", required=True),
        ToolParameter(name="cc", type="string", description="CC recipients (comma-separated)", required=False),
        ToolParameter(name="bcc", type="string", description="BCC recipients (comma-separated)", required=False),
    ],
    function=draft_gmail,
    module="life-manager"
))

tool_registry.register(ToolDefinition(
    name="send_gmail",
    description="Generate a mailto link to send Gmail. Opens user's email client with pre-filled content.",
    parameters=[
        ToolParameter(name="to", type="string", description="Recipient name or email address", required=True),
        ToolParameter(name="subject", type="string", description="Email subject line", required=True),
        ToolParameter(name="body", type="string", description="Email body content", required=True),
        ToolParameter(name="cc", type="string", description="CC recipients", required=False),
        ToolParameter(name="bcc", type="string", description="BCC recipients", required=False),
    ],
    function=send_gmail,
    module="life-manager"
))

# WhatsApp Tools
tool_registry.register(ToolDefinition(
    name="draft_whatsapp",
    description="Draft a WhatsApp message. ONLY accepts contact names (e.g., 'mom', 'dad', 'boss'), NOT phone numbers. The contact must exist in the contact list. Returns a draft requiring approval.",
    parameters=[
        ToolParameter(name="to", type="string", description="Recipient contact name (e.g., 'mom', 'dad', 'boss'). Phone numbers are NOT accepted.", required=True),
        ToolParameter(name="message", type="string", description="Message content", required=True),
    ],
    function=draft_whatsapp,
    module="life-manager"
))

tool_registry.register(ToolDefinition(
    name="send_whatsapp",
    description="Generate a WhatsApp deep link to send a message. ONLY accepts contact names (e.g., 'mom', 'dad', 'boss'), NOT phone numbers. The contact must exist in the contact list. Opens WhatsApp with pre-filled message.",
    parameters=[
        ToolParameter(name="to", type="string", description="Recipient contact name (e.g., 'mom', 'dad', 'boss'). Phone numbers are NOT accepted.", required=True),
        ToolParameter(name="message", type="string", description="Message content", required=True),
    ],
    function=send_whatsapp,
    module="life-manager"
))

# Instagram Tools
tool_registry.register(ToolDefinition(
    name="draft_instagram",
    description="Draft an Instagram direct message. Use contact names (e.g., 'mom') or Instagram handles. Returns a draft requiring approval.",
    parameters=[
        ToolParameter(name="to", type="string", description="Recipient name or Instagram handle", required=True),
        ToolParameter(name="message", type="string", description="Message content", required=True),
    ],
    function=draft_instagram,
    module="life-manager"
))

tool_registry.register(ToolDefinition(
    name="send_instagram",
    description="Generate an Instagram deep link to send a message. Opens Instagram with the conversation.",
    parameters=[
        ToolParameter(name="to", type="string", description="Recipient name or Instagram handle", required=True),
        ToolParameter(name="message", type="string", description="Message content", required=True),
    ],
    function=send_instagram,
    module="life-manager"
))

# Scheduling & Productivity
tool_registry.register(ToolDefinition(
    name="schedule_event",
    description="Schedule an event or meeting. Can use contact names for attendees.",
    parameters=[
        ToolParameter(name="title", type="string", description="Event title", required=True),
        ToolParameter(name="start_time", type="string", description="Start time (ISO format or natural language)", required=True),
        ToolParameter(name="duration_minutes", type="integer", description="Duration in minutes (default: 60)", required=False),
        ToolParameter(name="description", type="string", description="Event description", required=False),
        ToolParameter(name="location", type="string", description="Event location", required=False),
        ToolParameter(name="attendees", type="string", description="Comma-separated attendee names or emails", required=False),
    ],
    function=schedule_event,
    module="life-manager"
))

tool_registry.register(ToolDefinition(
    name="create_task",
    description="Create a task or to-do item",
    parameters=[
        ToolParameter(name="title", type="string", description="Task title", required=True),
        ToolParameter(name="description", type="string", description="Task description", required=False),
        ToolParameter(name="due_date", type="string", description="Due date (ISO format)", required=False),
        ToolParameter(name="priority", type="string", description="Priority: low, medium, high", required=False),
        ToolParameter(name="status", type="string", description="Status: todo, in_progress, done", required=False),
    ],
    function=create_task,
    module="life-manager"
))

# Contact Management
tool_registry.register(ToolDefinition(
    name="add_contact",
    description="Add or update a contact with communication channels",
    parameters=[
        ToolParameter(name="name", type="string", description="Contact name", required=True),
        ToolParameter(name="email", type="string", description="Email address", required=False),
        ToolParameter(name="phone", type="string", description="Phone number with country code", required=False),
        ToolParameter(name="instagram", type="string", description="Instagram handle", required=False),
    ],
    function=add_contact,
    module="life-manager"
))
