import argparse
import asyncio

import httpx


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--user-id")
    parser.add_argument("--article-id")
    parser.add_argument("--token")
    args = parser.parse_args()

    async with httpx.AsyncClient(base_url=args.base_url.rstrip("/")) as client:
        feed = await client.get(f"/user/{args.user_id}/articles") if args.user_id else None
        if feed is not None:
            print("feed", feed.status_code)

        if args.article_id:
            headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
            detail = await client.get(f"/articles/{args.article_id}", headers=headers)
            print("article", detail.status_code)
            search = await client.get("/search", params={"q": "FastAPI"})
            print("search", search.status_code)
            if args.token and args.user_id:
                analytics = await client.get(
                    f"/users/{args.user_id}/library/history/analytics",
                    headers=headers,
                )
                print("analytics", analytics.status_code)


if __name__ == "__main__":
    asyncio.run(main())
