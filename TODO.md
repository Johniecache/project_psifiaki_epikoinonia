1. Authentication & Security
  * Issue: Currently, AuthManager stores sessions only in memory and passwords are hashed correctly but no email/user uniqueness is enforced
  * Suggestion: Add persistant user storage, enforce uniqueness, add token expiration
2. Role & Permissions System
  * Issue: Roles exist but there is no permission check before sending messages, joining voice, or creating channels.
  * Suggestion: Add permission checks in EventServer, Implement hierarchy checks for role types, default roles on user creation
3. Channels
  * Issue: Channels are simple objects; no moderation or topic/name restrictions
  * Suggestion: Add channel categories, Implement channel locking / invite-only, Add message deletion and editing events broadcasted, Track last read message per user to support notifications
4. Messages
  * Issue: Messages are stored in memory and database but no edit/delete events propagate
  * Suggestion: Implement MESSAGE_UPDATE and MESSAGE_DELETE events, Add timestamps in ISO format for easier client parsing, 
5. Voice System
  * Issue: Only supports 1 channel per VoiceServer, Uses raw UDP; no NAT traversal or compression, No per-user volume control, push-to-talk, or disconnect detection
  * Suggestion: Refactor VoiceServer to support multiple channels, Consider using asyncio DatagramProtocol for better async UDP
6. Client
  * Issue: _voice_loop is blocking; can interfere with GUI if not careful, GUI and client controller logic are tightly coupled, No typing indicator, read receipts, or presence sync
  * Suggestion: Use asyncio for voice to avoid blocking GUI thread, Add PresenceStatus sync with server, Implement push-to-talk and voice channel user list
7. Server Architecture
  * Issue: EventServer and RealtimeServer are separate; some duplication
  * Suggestion: Merge message and event handling into one event loop, Add heartbeat / ping for connection health, Consider plugin hooks for easier extensibility (you already have Plugin
8. Database
  * Issue: SQLite is fine but no users table and no transactions for multi-step operations
  * Suggestion: Add users table, roles table, and permissions table, Use foreign keys to link messages → channels → servers → users, Wrap multi-inserts or deletes in transactions to ensure consistency
9. GUI
  * Issue: Basic; no server switching, friend list, or user avatars, Voice controls could be more dynamic
  * Suggestion: Add server tabs, DMs, presence indicators, Use after() loop to poll user/voice status instead of blocking, Add message reactions and threaded replies
10. General OOP & Code Quality
  * Make Channel, Server, User implement serialization/deserialization to dict for sending over network. Avoid duplicating code in EventServer and client.
  * Consider splitting ClientController into MessageClient + VoiceClient to separate responsibilities.
  * Add proper logging instead of print statements.
  * Use type hints consistently, including Optional
11. Optional
    * Private DMs
    * Mentions & notifications
    * Emojis/Gifs
    * Message Search
    * Persistant Voice with reconnect
    * Plugins
    * WebSocket transport for easier NAT traversal
