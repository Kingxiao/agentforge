# Third-Party OAuth Token Security Management

> Applicable scenarios: Agent calling Confluence / GitHub / Slack / Google Workspace APIs on behalf of the user.

## Four Major Risks

```
1. Plaintext storage → Database leak = Mass account hijacking
2. Token appears in logs → Log collection system becomes attack surface
3. No expiration rotation → Refresh Token long-lived = Persistent backdoor
4. Overly broad OAuth Scope → Attackers gain capabilities beyond what was intended
```

## Token Storage Solutions

| Scenario | Recommended Solution | Implementation |
|------|---------|------|
| Single-user CLI tool | OS Keychain | `keyring` (Python) / `keytar` (Node.js) |
| Multi-user web service | Encrypted database columns | Per-user independent encryption keys + KMS master key |
| Serverless / K8s | Secrets Manager | AWS Secrets Manager / GCP Secret Manager |

**Absolutely prohibited**:
- `ENV GITHUB_TOKEN=xxx` in Dockerfile (solidified into image layer, `docker history` visible)
- Token written to any log file (including DEBUG level logs)
- Token in URL parameters (HTTP server logs record URL query strings)

## Token Rotation Implementation

```python
import time

class OAuthTokenManager:
    REFRESH_BEFORE_EXPIRY_SECONDS = 300  # Refresh 5 minutes early to avoid race conditions

    def get_valid_token(self, user_id: str) -> str:
        token = self.storage.get_token(user_id)  # Retrieve from encrypted storage

        if token.expires_at - time.time() < self.REFRESH_BEFORE_EXPIRY_SECONDS:
            token = self._refresh(token.refresh_token)
            self.storage.save_token(user_id, token)  # Atomic update (write-first then replace, prevents window)

        return token.access_token

    def _refresh(self, refresh_token: str) -> "TokenPair":
        try:
            resp = requests.post(
                OAUTH_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": config.CLIENT_ID,
                    "client_secret": config.CLIENT_SECRET,  # Read from config file, no hardcoding
                },
                timeout=10,
            )
            resp.raise_for_status()
            return TokenPair.from_response(resp.json())
        except Exception:
            # Don't write exception details (containing tokens) to logs
            raise TokenExpiredError("OAuth token refresh failed — user re-auth required")
```

## Scope Minimization

```
Confluence read-only Agent example:
  ✗ write:confluence-content delete:confluence-content read:confluence-space.summary
  ✓ read:confluence-space.summary read:confluence-content

Declare required scope in Agent Spec (Phase 0); never request permissions "for convenience" that are broader than actually needed.
```

## Multi-Tenant Isolation

```python
def call_api(user_id: str, endpoint: str) -> dict:
    # Token manager enforces isolation by user_id
    # "Global token" mode prohibited (causes token mixing between users)
    access_token = token_manager.get_valid_token(user_id)  # user_id must be explicitly passed
    return http_client.get(endpoint, headers={"Authorization": f"Bearer {access_token}"})
```

## Revocation Handling

When a user revokes Agent authorization, must execute immediately (cannot wait for TTL expiration):

```python
async def handle_oauth_revocation(user_id: str):
    token = storage.get_token(user_id)

    # 1. Revoke with OAuth Provider (revoke first, then delete, avoids window)
    await http_client.post(
        OAUTH_REVOKE_URL,
        data={"token": token.refresh_token, "token_type_hint": "refresh_token"},
    )

    # 2. Delete local storage
    storage.delete_token(user_id)

    # 3. Invalidate in-memory cache (if any in-process cache exists)
    token_cache.invalidate(user_id)
```

## Global Lock for Multi-Provider Concurrent Refresh

When an Agent holds tokens from multiple OAuth Providers simultaneously (Slack + Notion + GitHub), and concurrent requests trigger multiple tokens approaching expiration, lock-free refresh leads to races: the same token gets refreshed multiple times, the old refresh token is consumed and invalidated, causing all subsequent requests to fail.

```python
import asyncio
from typing import ClassVar

class OAuthTokenManager:
    # Lock at (user_id, provider) granularity; different users / different Providers don't block each other
    _locks: ClassVar[dict[tuple, asyncio.Lock]] = {}
    _locks_meta: ClassVar[asyncio.Lock] = asyncio.Lock()

    async def get_valid_token(self, user_id: str, provider: str) -> str:
        lock_key = (user_id, provider)
        
        # Create lock on-demand (global meta-lock protects dict writes)
        async with self._locks_meta:
            if lock_key not in self._locks:
                self._locks[lock_key] = asyncio.Lock()
        
        async with self._locks[lock_key]:
            token = self.storage.get_token(user_id, provider)
            
            # Double-check: after acquiring lock, verify validity again
            # Prevents redundant refresh when another coroutine already refreshed while waiting
            if not token.is_expiring_soon():
                return token.access_token
            
            new_token = await self._refresh(token.refresh_token, provider)
            self.storage.save_token(user_id, provider, new_token)
            return new_token.access_token
```

**Key principles**:
- Lock granularity is `(user_id, provider)`, not global (global lock serializes all users' all requests)
- Double-check prevents re-refresh when another coroutine has already refreshed while waiting for the lock
- Lock should be in-process (asyncio.Lock); distributed scenarios need Redis distributed lock
