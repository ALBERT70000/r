"""
Social Media Skill for R CLI.

Manage social media accounts:
- Twitter/X, Instagram, Facebook, LinkedIn
- Discord, Telegram, WhatsApp Business
- Read messages, comments, mentions
- Post updates and responses
- Unified inbox for all platforms
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from r_cli.core.agent import Skill
from r_cli.core.llm import Tool

logger = logging.getLogger(__name__)


class SocialMediaSkill(Skill):
    """Skill for social media management."""

    name = "social"
    description = "Social media manager: read/respond to messages across Twitter, Instagram, Facebook, LinkedIn, Discord, Telegram"

    # Platform configurations
    PLATFORMS = {
        "twitter": {
            "name": "Twitter/X",
            "api_base": "https://api.twitter.com/2",
            "env_vars": ["TWITTER_BEARER_TOKEN", "TWITTER_API_KEY", "TWITTER_API_SECRET"],
        },
        "instagram": {
            "name": "Instagram",
            "api_base": "https://graph.instagram.com",
            "env_vars": ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ID"],
        },
        "facebook": {
            "name": "Facebook",
            "api_base": "https://graph.facebook.com/v18.0",
            "env_vars": ["FACEBOOK_ACCESS_TOKEN", "FACEBOOK_PAGE_ID"],
        },
        "linkedin": {
            "name": "LinkedIn",
            "api_base": "https://api.linkedin.com/v2",
            "env_vars": ["LINKEDIN_ACCESS_TOKEN"],
        },
        "discord": {
            "name": "Discord",
            "api_base": "https://discord.com/api/v10",
            "env_vars": ["DISCORD_BOT_TOKEN"],
        },
        "telegram": {
            "name": "Telegram",
            "api_base": "https://api.telegram.org",
            "env_vars": ["TELEGRAM_BOT_TOKEN"],
        },
    }

    def __init__(self, config=None):
        super().__init__(config)
        self._messages_cache = []
        self._response_queue = []

    def get_tools(self) -> list[Tool]:
        return [
            # Configuration
            Tool(
                name="social_config",
                description="Show social media configuration and connected platforms",
                parameters={"type": "object", "properties": {}},
                handler=self.show_config,
            ),
            Tool(
                name="social_connect",
                description="Connect a social media platform",
                parameters={
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": list(self.PLATFORMS.keys()),
                            "description": "Platform to connect",
                        },
                        "credentials": {
                            "type": "string",
                            "description": "JSON with credentials (token, api_key, etc)",
                        },
                    },
                    "required": ["platform"],
                },
                handler=self.connect_platform,
            ),
            # Reading messages
            Tool(
                name="social_inbox",
                description="Get unified inbox with messages from all connected platforms",
                parameters={
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": ["all"] + list(self.PLATFORMS.keys()),
                            "description": "Filter by platform (default: all)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max messages to fetch (default: 20)",
                        },
                        "unread_only": {
                            "type": "boolean",
                            "description": "Only show unread messages",
                        },
                    },
                },
                handler=self.get_inbox,
            ),
            Tool(
                name="social_mentions",
                description="Get mentions and comments across platforms",
                parameters={
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": ["all"] + list(self.PLATFORMS.keys()),
                            "description": "Filter by platform",
                        },
                        "since": {
                            "type": "string",
                            "description": "Since date (YYYY-MM-DD)",
                        },
                    },
                },
                handler=self.get_mentions,
            ),
            Tool(
                name="social_comments",
                description="Get comments on your posts",
                parameters={
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": list(self.PLATFORMS.keys()),
                            "description": "Platform to check",
                        },
                        "post_id": {
                            "type": "string",
                            "description": "Post ID (optional - gets all recent if not specified)",
                        },
                    },
                },
                handler=self.get_comments,
            ),
            # Responding
            Tool(
                name="social_reply",
                description="Reply to a message or comment",
                parameters={
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": list(self.PLATFORMS.keys()),
                            "description": "Platform",
                        },
                        "message_id": {
                            "type": "string",
                            "description": "ID of message/comment to reply to",
                        },
                        "text": {
                            "type": "string",
                            "description": "Reply text",
                        },
                    },
                    "required": ["platform", "message_id", "text"],
                },
                handler=self.reply_message,
            ),
            Tool(
                name="social_post",
                description="Post new content to a platform",
                parameters={
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": list(self.PLATFORMS.keys()),
                            "description": "Platform to post to",
                        },
                        "text": {
                            "type": "string",
                            "description": "Post content",
                        },
                        "media": {
                            "type": "string",
                            "description": "Path to media file (optional)",
                        },
                    },
                    "required": ["platform", "text"],
                },
                handler=self.post_content,
            ),
            Tool(
                name="social_dm",
                description="Send a direct message",
                parameters={
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": list(self.PLATFORMS.keys()),
                            "description": "Platform",
                        },
                        "recipient": {
                            "type": "string",
                            "description": "Username or user ID",
                        },
                        "text": {
                            "type": "string",
                            "description": "Message text",
                        },
                    },
                    "required": ["platform", "recipient", "text"],
                },
                handler=self.send_dm,
            ),
            # Queue management
            Tool(
                name="social_queue_add",
                description="Add a response to the queue for review before sending",
                parameters={
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": list(self.PLATFORMS.keys()),
                        },
                        "message_id": {"type": "string"},
                        "response": {"type": "string"},
                        "priority": {
                            "type": "string",
                            "enum": ["high", "normal", "low"],
                        },
                    },
                    "required": ["platform", "message_id", "response"],
                },
                handler=self.queue_add,
            ),
            Tool(
                name="social_queue_list",
                description="Show queued responses pending review",
                parameters={"type": "object", "properties": {}},
                handler=self.queue_list,
            ),
            Tool(
                name="social_queue_send",
                description="Send all approved queued responses",
                parameters={
                    "type": "object",
                    "properties": {
                        "queue_id": {
                            "type": "string",
                            "description": "Specific queue ID to send (or 'all')",
                        },
                    },
                },
                handler=self.queue_send,
            ),
            # Analytics
            Tool(
                name="social_stats",
                description="Get social media statistics and engagement metrics",
                parameters={
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": ["all"] + list(self.PLATFORMS.keys()),
                        },
                        "period": {
                            "type": "string",
                            "enum": ["today", "week", "month"],
                        },
                    },
                },
                handler=self.get_stats,
            ),
        ]

    def _get_credentials(self, platform: str) -> dict:
        """Get credentials for a platform from environment variables."""
        if platform not in self.PLATFORMS:
            return {}

        creds = {}
        for env_var in self.PLATFORMS[platform]["env_vars"]:
            value = os.environ.get(env_var)
            if value:
                key = env_var.lower().replace(f"{platform}_", "")
                creds[key] = value

        return creds

    def _is_connected(self, platform: str) -> bool:
        """Check if a platform is connected."""
        creds = self._get_credentials(platform)
        return len(creds) > 0

    def _make_request(
        self,
        platform: str,
        endpoint: str,
        method: str = "GET",
        data: Optional[dict] = None,
    ) -> dict:
        """Make an API request to a platform."""
        try:
            import httpx

            creds = self._get_credentials(platform)
            if not creds:
                return {"error": f"Platform {platform} not connected"}

            api_base = self.PLATFORMS[platform]["api_base"]
            headers = self._get_auth_headers(platform, creds)

            with httpx.Client(timeout=30) as client:
                if method == "GET":
                    response = client.get(f"{api_base}{endpoint}", headers=headers)
                elif method == "POST":
                    response = client.post(
                        f"{api_base}{endpoint}",
                        headers=headers,
                        json=data,
                    )
                else:
                    return {"error": f"Unsupported method: {method}"}

                if response.status_code >= 400:
                    return {"error": f"API error: {response.status_code}", "detail": response.text}

                return response.json()

        except ImportError:
            return {"error": "httpx not installed. Run: pip install httpx"}
        except Exception as e:
            return {"error": str(e)}

    def _get_auth_headers(self, platform: str, creds: dict) -> dict:
        """Get authentication headers for a platform."""
        headers = {"Content-Type": "application/json"}

        if platform == "twitter":
            if "bearer_token" in creds:
                headers["Authorization"] = f"Bearer {creds['bearer_token']}"
        elif platform == "discord":
            if "bot_token" in creds:
                headers["Authorization"] = f"Bot {creds['bot_token']}"
        elif platform == "telegram":
            pass  # Token is in URL
        elif platform in ("instagram", "facebook"):
            pass  # Token is in query params
        elif platform == "linkedin":
            if "access_token" in creds:
                headers["Authorization"] = f"Bearer {creds['access_token']}"

        return headers

    # =========================================================================
    # Tool Handlers
    # =========================================================================

    def show_config(self) -> str:
        """Show configuration and connected platforms."""
        result = ["📱 Social Media Configuration\n"]
        result.append("=" * 40)

        connected = []
        not_connected = []

        for platform, info in self.PLATFORMS.items():
            if self._is_connected(platform):
                connected.append(f"  ✅ {info['name']} - Connected")
            else:
                not_connected.append(f"  ❌ {info['name']} - Not configured")
                not_connected.append(f"     Required: {', '.join(info['env_vars'])}")

        if connected:
            result.append("\nConnected platforms:")
            result.extend(connected)

        if not_connected:
            result.append("\nNot connected:")
            result.extend(not_connected)

        result.append("\n" + "=" * 40)
        result.append("\nTo connect a platform, set environment variables:")
        result.append("  export TWITTER_BEARER_TOKEN='your_token'")
        result.append("  export TELEGRAM_BOT_TOKEN='your_token'")
        result.append("  etc.")

        return "\n".join(result)

    def connect_platform(
        self,
        platform: str,
        credentials: Optional[str] = None,
    ) -> str:
        """Connect a platform (shows instructions)."""
        if platform not in self.PLATFORMS:
            return f"Error: Unknown platform '{platform}'"

        info = self.PLATFORMS[platform]
        result = [f"🔗 Connecting {info['name']}\n"]

        if credentials:
            try:
                creds = json.loads(credentials)
                # In a real implementation, this would store credentials securely
                result.append("⚠️  For security, credentials should be set via environment variables:")
            except json.JSONDecodeError:
                return "Error: Invalid JSON for credentials"

        result.append(f"\nRequired environment variables for {info['name']}:")
        for env_var in info["env_vars"]:
            result.append(f"  export {env_var}='your_value'")

        result.append(f"\nAPI Documentation: {self._get_docs_url(platform)}")

        return "\n".join(result)

    def _get_docs_url(self, platform: str) -> str:
        """Get documentation URL for a platform."""
        docs = {
            "twitter": "https://developer.twitter.com/en/docs",
            "instagram": "https://developers.facebook.com/docs/instagram-api",
            "facebook": "https://developers.facebook.com/docs/graph-api",
            "linkedin": "https://docs.microsoft.com/en-us/linkedin/",
            "discord": "https://discord.com/developers/docs",
            "telegram": "https://core.telegram.org/bots/api",
        }
        return docs.get(platform, "")

    def get_inbox(
        self,
        platform: str = "all",
        limit: int = 20,
        unread_only: bool = False,
    ) -> str:
        """Get unified inbox."""
        result = ["📥 Unified Inbox\n"]
        messages = []

        platforms_to_check = (
            list(self.PLATFORMS.keys()) if platform == "all" else [platform]
        )

        for plat in platforms_to_check:
            if not self._is_connected(plat):
                continue

            plat_messages = self._fetch_messages(plat, limit)
            for msg in plat_messages:
                msg["platform"] = plat
                messages.append(msg)

        # Sort by timestamp
        messages.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        if unread_only:
            messages = [m for m in messages if not m.get("read", False)]

        messages = messages[:limit]

        if not messages:
            result.append("No messages found.")
            if platform == "all":
                result.append("\nTip: Make sure at least one platform is connected.")
            return "\n".join(result)

        for i, msg in enumerate(messages, 1):
            plat_name = self.PLATFORMS[msg["platform"]]["name"]
            result.append(f"{i}. [{plat_name}] @{msg.get('from', 'unknown')}")
            result.append(f"   {msg.get('text', '')[:100]}")
            result.append(f"   ID: {msg.get('id', '')} | {msg.get('timestamp', '')}")
            result.append("")

        return "\n".join(result)

    def _fetch_messages(self, platform: str, limit: int) -> list:
        """Fetch messages from a specific platform."""
        messages = []

        if platform == "twitter":
            # Twitter DMs endpoint
            response = self._make_request(platform, "/dm_events", "GET")
            if "data" in response:
                for dm in response["data"][:limit]:
                    messages.append({
                        "id": dm.get("id"),
                        "from": dm.get("sender_id"),
                        "text": dm.get("text"),
                        "timestamp": dm.get("created_at"),
                        "type": "dm",
                    })

        elif platform == "telegram":
            creds = self._get_credentials(platform)
            if "bot_token" in creds:
                import httpx
                try:
                    response = httpx.get(
                        f"https://api.telegram.org/bot{creds['bot_token']}/getUpdates",
                        timeout=30,
                    ).json()
                    if response.get("ok"):
                        for update in response.get("result", [])[:limit]:
                            msg = update.get("message", {})
                            messages.append({
                                "id": str(update.get("update_id")),
                                "from": msg.get("from", {}).get("username", "unknown"),
                                "text": msg.get("text", ""),
                                "timestamp": datetime.fromtimestamp(
                                    msg.get("date", 0)
                                ).isoformat(),
                                "type": "message",
                            })
                except Exception:
                    pass

        elif platform == "discord":
            # Discord requires specific channel ID
            pass

        elif platform == "instagram":
            creds = self._get_credentials(platform)
            if "access_token" in creds:
                # Instagram conversations endpoint
                pass

        elif platform == "facebook":
            creds = self._get_credentials(platform)
            if "access_token" in creds and "page_id" in creds:
                # Facebook page conversations
                pass

        return messages

    def get_mentions(
        self,
        platform: str = "all",
        since: Optional[str] = None,
    ) -> str:
        """Get mentions across platforms."""
        result = ["🔔 Mentions\n"]
        mentions = []

        platforms_to_check = (
            list(self.PLATFORMS.keys()) if platform == "all" else [platform]
        )

        for plat in platforms_to_check:
            if not self._is_connected(plat):
                continue

            plat_mentions = self._fetch_mentions(plat)
            for mention in plat_mentions:
                mention["platform"] = plat
                mentions.append(mention)

        if not mentions:
            result.append("No mentions found.")
            return "\n".join(result)

        for i, mention in enumerate(mentions, 1):
            plat_name = self.PLATFORMS[mention["platform"]]["name"]
            result.append(f"{i}. [{plat_name}] @{mention.get('from', 'unknown')}")
            result.append(f"   {mention.get('text', '')[:100]}")
            result.append(f"   ID: {mention.get('id', '')}")
            result.append("")

        return "\n".join(result)

    def _fetch_mentions(self, platform: str) -> list:
        """Fetch mentions from a platform."""
        mentions = []

        if platform == "twitter":
            # Twitter mentions timeline
            response = self._make_request(platform, "/users/me/mentions", "GET")
            if "data" in response:
                for tweet in response["data"]:
                    mentions.append({
                        "id": tweet.get("id"),
                        "from": tweet.get("author_id"),
                        "text": tweet.get("text"),
                        "timestamp": tweet.get("created_at"),
                        "type": "mention",
                    })

        return mentions

    def get_comments(
        self,
        platform: str,
        post_id: Optional[str] = None,
    ) -> str:
        """Get comments on posts."""
        if not self._is_connected(platform):
            return f"Error: {platform} not connected"

        result = [f"💬 Comments on {self.PLATFORMS[platform]['name']}\n"]

        # Platform-specific comment fetching
        comments = self._fetch_comments(platform, post_id)

        if not comments:
            result.append("No comments found.")
            return "\n".join(result)

        for i, comment in enumerate(comments, 1):
            result.append(f"{i}. @{comment.get('from', 'unknown')}")
            result.append(f"   {comment.get('text', '')}")
            result.append(f"   ID: {comment.get('id', '')}")
            result.append("")

        return "\n".join(result)

    def _fetch_comments(self, platform: str, post_id: Optional[str]) -> list:
        """Fetch comments from a platform."""
        comments = []

        if platform == "instagram":
            creds = self._get_credentials(platform)
            if "access_token" in creds and post_id:
                # Instagram comments endpoint
                pass

        elif platform == "facebook":
            creds = self._get_credentials(platform)
            if "access_token" in creds and post_id:
                # Facebook comments endpoint
                pass

        return comments

    def reply_message(
        self,
        platform: str,
        message_id: str,
        text: str,
    ) -> str:
        """Reply to a message or comment."""
        if not self._is_connected(platform):
            return f"Error: {platform} not connected"

        result = self._send_reply(platform, message_id, text)

        if result.get("success"):
            return f"✅ Reply sent on {self.PLATFORMS[platform]['name']}"
        else:
            return f"❌ Error: {result.get('error', 'Unknown error')}"

    def _send_reply(self, platform: str, message_id: str, text: str) -> dict:
        """Send a reply on a platform."""
        if platform == "twitter":
            return self._make_request(
                platform,
                "/tweets",
                "POST",
                {"text": text, "reply": {"in_reply_to_tweet_id": message_id}},
            )

        elif platform == "telegram":
            creds = self._get_credentials(platform)
            if "bot_token" in creds:
                import httpx
                try:
                    response = httpx.post(
                        f"https://api.telegram.org/bot{creds['bot_token']}/sendMessage",
                        json={"chat_id": message_id, "text": text},
                        timeout=30,
                    ).json()
                    if response.get("ok"):
                        return {"success": True}
                    return {"error": response.get("description")}
                except Exception as e:
                    return {"error": str(e)}

        return {"error": "Platform not supported for replies"}

    def post_content(
        self,
        platform: str,
        text: str,
        media: Optional[str] = None,
    ) -> str:
        """Post content to a platform."""
        if not self._is_connected(platform):
            return f"Error: {platform} not connected"

        result = self._create_post(platform, text, media)

        if result.get("success"):
            return f"✅ Posted to {self.PLATFORMS[platform]['name']}\nPost ID: {result.get('id', 'N/A')}"
        else:
            return f"❌ Error: {result.get('error', 'Unknown error')}"

    def _create_post(self, platform: str, text: str, media: Optional[str]) -> dict:
        """Create a post on a platform."""
        if platform == "twitter":
            return self._make_request(platform, "/tweets", "POST", {"text": text})

        elif platform == "telegram":
            creds = self._get_credentials(platform)
            if "bot_token" in creds:
                # Telegram requires a chat_id, so this is for channels
                return {"error": "Use social_dm for Telegram messages"}

        return {"error": "Platform not supported for posting"}

    def send_dm(
        self,
        platform: str,
        recipient: str,
        text: str,
    ) -> str:
        """Send a direct message."""
        if not self._is_connected(platform):
            return f"Error: {platform} not connected"

        result = self._send_direct_message(platform, recipient, text)

        if result.get("success"):
            return f"✅ DM sent to @{recipient} on {self.PLATFORMS[platform]['name']}"
        else:
            return f"❌ Error: {result.get('error', 'Unknown error')}"

    def _send_direct_message(self, platform: str, recipient: str, text: str) -> dict:
        """Send a DM on a platform."""
        if platform == "telegram":
            creds = self._get_credentials(platform)
            if "bot_token" in creds:
                import httpx
                try:
                    response = httpx.post(
                        f"https://api.telegram.org/bot{creds['bot_token']}/sendMessage",
                        json={"chat_id": recipient, "text": text},
                        timeout=30,
                    ).json()
                    if response.get("ok"):
                        return {"success": True, "id": response["result"]["message_id"]}
                    return {"error": response.get("description")}
                except Exception as e:
                    return {"error": str(e)}

        return {"error": "Platform not supported for DMs"}

    def queue_add(
        self,
        platform: str,
        message_id: str,
        response: str,
        priority: str = "normal",
    ) -> str:
        """Add response to queue."""
        queue_item = {
            "id": f"q_{len(self._response_queue) + 1}",
            "platform": platform,
            "message_id": message_id,
            "response": response,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }

        self._response_queue.append(queue_item)

        return f"✅ Added to queue: {queue_item['id']}\nPriority: {priority}\nResponse: {response[:50]}..."

    def queue_list(self) -> str:
        """List queued responses."""
        if not self._response_queue:
            return "📭 Response queue is empty"

        result = ["📋 Response Queue\n"]

        for item in self._response_queue:
            status_icon = "⏳" if item["status"] == "pending" else "✅"
            plat_name = self.PLATFORMS.get(item["platform"], {}).get("name", item["platform"])

            result.append(f"{status_icon} [{item['id']}] {plat_name}")
            result.append(f"   To: {item['message_id']}")
            result.append(f"   Response: {item['response'][:60]}...")
            result.append(f"   Priority: {item['priority']}")
            result.append("")

        return "\n".join(result)

    def queue_send(self, queue_id: Optional[str] = None) -> str:
        """Send queued responses."""
        if not self._response_queue:
            return "Queue is empty"

        sent = 0
        errors = []

        items_to_send = self._response_queue if queue_id in (None, "all") else [
            item for item in self._response_queue if item["id"] == queue_id
        ]

        for item in items_to_send:
            if item["status"] != "pending":
                continue

            result = self._send_reply(item["platform"], item["message_id"], item["response"])

            if result.get("success"):
                item["status"] = "sent"
                sent += 1
            else:
                errors.append(f"{item['id']}: {result.get('error')}")

        # Remove sent items
        self._response_queue = [item for item in self._response_queue if item["status"] == "pending"]

        result_text = f"✅ Sent: {sent} responses"
        if errors:
            result_text += f"\n❌ Errors:\n" + "\n".join(errors)

        return result_text

    def get_stats(
        self,
        platform: str = "all",
        period: str = "week",
    ) -> str:
        """Get social media statistics."""
        result = [f"📊 Social Media Stats ({period})\n"]

        platforms_to_check = (
            list(self.PLATFORMS.keys()) if platform == "all" else [platform]
        )

        for plat in platforms_to_check:
            if not self._is_connected(plat):
                continue

            stats = self._fetch_stats(plat, period)
            plat_name = self.PLATFORMS[plat]["name"]

            result.append(f"\n{plat_name}:")
            result.append(f"  Messages received: {stats.get('messages', 'N/A')}")
            result.append(f"  Mentions: {stats.get('mentions', 'N/A')}")
            result.append(f"  Responses sent: {stats.get('responses', 'N/A')}")
            result.append(f"  Avg response time: {stats.get('avg_response_time', 'N/A')}")

        return "\n".join(result)

    def _fetch_stats(self, platform: str, period: str) -> dict:
        """Fetch statistics from a platform."""
        # This would fetch real stats from the platform API
        return {
            "messages": 0,
            "mentions": 0,
            "responses": 0,
            "avg_response_time": "N/A",
        }

    def execute(self, **kwargs) -> str:
        """Direct skill execution."""
        action = kwargs.get("action", "config")

        if action == "config":
            return self.show_config()
        elif action == "inbox":
            return self.get_inbox(
                kwargs.get("platform", "all"),
                kwargs.get("limit", 20),
            )
        elif action == "mentions":
            return self.get_mentions(kwargs.get("platform", "all"))
        elif action == "stats":
            return self.get_stats(
                kwargs.get("platform", "all"),
                kwargs.get("period", "week"),
            )
        else:
            return f"Unknown action: {action}"
