"""
Contact Management Service

Provides contact resolution and management for life-manager features.
Maps contact names to their communication channels (email, phone, Instagram).
"""

from typing import Optional, Dict, Any
import json
from backend.core.logger import get_logger

logger = get_logger(__name__)


class Contact:
    """Represents a contact with multiple communication channels."""
    
    def __init__(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        instagram: Optional[str] = None,
        aliases: Optional[list[str]] = None
    ):
        self.name = name
        self.email = email
        self.phone = phone
        self.instagram = instagram
        self.aliases = aliases or []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert contact to dictionary."""
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "instagram": self.instagram,
            "aliases": self.aliases
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Contact":
        """Create contact from dictionary."""
        return cls(
            name=data["name"],
            email=data.get("email"),
            phone=data.get("phone"),
            instagram=data.get("instagram"),
            aliases=data.get("aliases", [])
        )


class ContactManager:
    """
    Manages contact resolution and lookups.
    
    In production, this would integrate with:
    - Google Contacts API
    - Phone contacts database
    - Instagram friends API
    
    For now, maintains an in-memory contact store.
    """
    
    def __init__(self):
        # Default contacts for demo/testing
        self._contacts: Dict[str, Contact] = {
            "mom": Contact(
                name="Mom",
                email="mom@example.com",
                phone="+1234567890",
                instagram="@mom_instagram",
                aliases=["mother", "mama", "mum"]
            ),
            "dad": Contact(
                name="Dad",
                email="dad@example.com",
                phone="+1234567891",
                instagram="@dad_instagram",
                aliases=["father", "papa", "pop"]
            ),
            "boss": Contact(
                name="Boss",
                email="boss@company.com",
                phone="+1234567892",
                instagram="@boss_instagram",
                aliases=["manager", "supervisor"]
            ),
        }
        logger.info("contact_manager_initialized", contact_count=len(self._contacts))
    
    def resolve_contact(self, name: str) -> Optional[Contact]:
        """
        Resolve a contact name to a Contact object.
        
        Performs case-insensitive matching on:
        - Primary name
        - Aliases
        
        Args:
            name: Contact name or alias
            
        Returns:
            Contact object if found, None otherwise
        """
        name_lower = name.lower().strip()
        
        # Direct name match
        if name_lower in self._contacts:
            contact = self._contacts[name_lower]
            logger.info("contact_resolved", name=name, contact=contact.name)
            return contact
        
        # Alias match
        for contact_key, contact in self._contacts.items():
            if name_lower in [alias.lower() for alias in contact.aliases]:
                logger.info("contact_resolved_via_alias", name=name, contact=contact.name, alias=name)
                return contact
        
        logger.warning("contact_not_found", name=name)
        return None
    
    def get_email(self, name: str) -> Optional[str]:
        """Get email address for a contact."""
        contact = self.resolve_contact(name)
        return contact.email if contact else None
    
    def get_phone(self, name: str) -> Optional[str]:
        """Get phone number for a contact."""
        contact = self.resolve_contact(name)
        return contact.phone if contact else None
    
    def get_instagram(self, name: str) -> Optional[str]:
        """Get Instagram handle for a contact."""
        contact = self.resolve_contact(name)
        return contact.instagram if contact else None
    
    def add_contact(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        instagram: Optional[str] = None,
        aliases: Optional[list[str]] = None
    ) -> Contact:
        """
        Add or update a contact.
        
        Args:
            name: Contact name
            email: Email address
            phone: Phone number
            instagram: Instagram handle
            aliases: List of name aliases
            
        Returns:
            Created/updated Contact object
        """
        contact = Contact(
            name=name,
            email=email,
            phone=phone,
            instagram=instagram,
            aliases=aliases
        )
        self._contacts[name.lower()] = contact
        logger.info("contact_added", name=name)
        return contact
    
    def list_contacts(self) -> list[Contact]:
        """Get all contacts."""
        return list(self._contacts.values())
    
    def remove_contact(self, name: str) -> bool:
        """
        Remove a contact.
        
        Args:
            name: Contact name
            
        Returns:
            True if contact was removed, False if not found
        """
        name_lower = name.lower()
        if name_lower in self._contacts:
            del self._contacts[name_lower]
            logger.info("contact_removed", name=name)
            return True
        return False


# Global singleton instance
contact_manager = ContactManager()

