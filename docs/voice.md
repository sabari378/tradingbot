# Voice

Siri Shortcuts and Android assistant actions should POST text to `/api/v1/voice/command` over HTTPS. Read-only intents are parsed deterministically. Approve, reject, and close intents return a confirmation requirement and must use stronger authentication; broker credentials never enter a shortcut or voice payload.
