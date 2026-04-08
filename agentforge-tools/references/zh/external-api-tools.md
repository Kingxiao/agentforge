# 外部 API 工具详细实现参考

> 主文档精简后的完整实现代码。主文档保留概念和接口声明，本文件保留可直接复用的代码。

## 幂等性完整实现

```python
def create_issue_tool(title: str, body: str, idempotency_key: str | None = None) -> dict:
    headers = {}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    # 先查后写（check-then-act）兜底方案
    existing = github_api.search_issues(f"title:{title} is:open")
    if existing.total_count > 0:
        return {"status": "already_exists", "issue": existing.items[0]}
    return github_api.post("/issues", {"title": title, "body": body}, headers=headers)
```

## 指数退避重试实现

```python
import time, random

def call_with_retry(fn, max_retries: int = 3, base_delay: float = 1.0):
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except RateLimitError as e:
            if attempt == max_retries:
                raise
            # retry-after header 优先（精确），否则指数退避 + jitter
            delay = float(e.headers.get("retry-after", base_delay * (2 ** attempt) + random.uniform(0, 1)))
            time.sleep(delay)
        except (NetworkError, ServiceUnavailableError):
            if attempt == max_retries:
                raise
            time.sleep(base_delay * (2 ** attempt))
```

**重试原则**：
- 只重试幂等操作，或已确认幂等的非幂等操作
- 只重试可恢复错误（5xx、超时、限流）；4xx 不重试
- 最大重试次数写入工具 metadata

## 单工具客户端限速实现

```python
import time

class RateLimitedTool:
    def __init__(self, rps: float = 10):
        self._last_call = 0
        self._min_interval = 1.0 / rps

    def call(self, input: dict) -> dict:
        elapsed = time.time() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.time()

        result = self._execute(input)
        return {
            **result,
            "_rate_limit_remaining": result.headers.get("x-ratelimit-remaining"),
            "_rate_limit_reset": result.headers.get("x-ratelimit-reset"),
        }
```

## 分页工具完整实现（PaginatedAPITool）

```python
class PaginatedAPITool(Tool):
    MAX_PAGES = 10      # 硬上限，防止无限翻页
    PAGE_SIZE = 50
    TOKEN_BUDGET = 4000  # 返回给 Agent 的最大 token

    def call(self, input: dict) -> dict:
        all_items = []
        cursor = input.get("cursor")  # 支持从外部传入游标续页
        pages_fetched = 0

        while pages_fetched < self.MAX_PAGES:
            response = self._fetch_page(
                query=input["query"],
                cursor=cursor,
                limit=self.PAGE_SIZE,
            )
            all_items.extend(response["items"])
            pages_fetched += 1

            if not response.get("has_more") or not response.get("next_cursor"):
                break
            cursor = response["next_cursor"]

            # Token 预算检查：超限则截断并告知 Agent 游标位置
            if self._estimate_tokens(all_items) > self.TOKEN_BUDGET:
                return {
                    "items": all_items,
                    "truncated": True,
                    "total_fetched": len(all_items),
                    "next_cursor": cursor,
                    "note": (
                        f"Results truncated at {len(all_items)} items to fit token budget. "
                        f"Use cursor='{cursor}' to continue."
                    ),
                }

        return {"items": all_items, "truncated": False, "total_fetched": len(all_items)}
```

## 多工具共享限速器（进程级单例）

```python
import asyncio
from typing import ClassVar

_shared_limiters: dict[str, asyncio.Semaphore] = {}

def get_shared_limiter(endpoint_key: str, rpm: int):
    """
    所有调用同一 endpoint 的工具共享同一个 RateLimiter 实例。
    endpoint_key 示例: 'confluence.company.com', 'api.github.com'
    """
    if endpoint_key not in _shared_limiters:
        _shared_limiters[endpoint_key] = RateLimiter(rate=rpm, period=60)
    return _shared_limiters[endpoint_key]

# 使用示例：两个工具共享同一个 Confluence API 限速器
class ConfluenceSearchTool(Tool):
    _limiter: ClassVar = get_shared_limiter("confluence", rpm=5)

    async def call(self, input: dict) -> dict:
        async with self._limiter:
            return await self._search(input)

class ConfluenceReadPageTool(Tool):
    _limiter: ClassVar = get_shared_limiter("confluence", rpm=5)  # 同一实例

    async def call(self, input: dict) -> dict:
        async with self._limiter:
            return await self._read_page(input)
```
