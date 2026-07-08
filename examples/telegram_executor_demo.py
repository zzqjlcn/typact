import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Annotated, Any, Literal, TypeAlias

import httpx
from pydantic import BaseModel, Field

from falcon import (
    Body,
    CallableTokenProvider,
    Form,
    HttpClient,
    HttpxRuntime,
    InterceptorChain,
    Path,
    RefreshableBearerTokenInterceptor,
)


QueryType: TypeAlias = Literal["default", "txt", "audio", "image", "file", "video"]
LimitInt: TypeAlias = Annotated[int, Field(ge=1, le=5000, description="分页条数，1~5000")]
TargetType: TypeAlias = Literal["sender", "chat"]


_DECODE_MESSAGE_TYPE: dict[str | None, str] = {
    "1": "文本",
    "3": "图片",
    "5": "附件",
    "7": "合并转发信息",
    "8": "拍一拍",
    "9": "外部链接",
    "10": "分享名片",
    "11": "接龙",
    "12": "笔记",
    "13": "表情",
    "14": "红包",
    "15": "收款",
    "17": "位置",
    "18": "共享位置",
    "19": "语音视频通话",
    "20": "转账",
    "22": "直播",
    "34": "语音",
    "36": "未知消息",
    "37": "好友验证",
    "40": "未知消息",
    "43": "视频",
    "44": "视频",
    "4000": "未知消息",
    "9999": "系统消息",
    "None": "未知消息",
}


@dataclass
class TelegramConfig:
    base_url: str
    username: str
    password: str
    sender_path: str
    chat_path: str
    verify_ssl: bool = True
    default_timeout: float = 30


class ChatMessage(BaseModel):
    message_id: str | None = None
    chat_id: str | None = None
    sender_id: str | None = None
    content: str | None = None
    send_time: datetime
    message_type: str | None = None


class TelegramLoginApi:
    def __init__(self, config: TelegramConfig):
        self.client = HttpClient(
            base_url=config.base_url,
            client_runtime=HttpxRuntime(
                httpx.AsyncClient(
                    verify=config.verify_ssl,
                    timeout=config.default_timeout,
                )
            ),
        )

        @self.client.post("/auth/login")
        async def login(
            name: str = Form(),
            password: str = Form(),
        ) -> dict[str, Any]:
            pass

        self.login = login

    async def close(self):
        await self.client.close()


class TelegramMessageApi:
    def __init__(
        self,
        config: TelegramConfig,
        token_provider: CallableTokenProvider,
    ):
        self.client = HttpClient(
            base_url=config.base_url,
            client_runtime=HttpxRuntime(
                httpx.AsyncClient(
                    verify=config.verify_ssl,
                    timeout=config.default_timeout,
                )
            ),
            headers={
                "Content-Type": "application/json",
            },
            interceptor_chain=InterceptorChain(
                request_interceptors=[
                    RefreshableBearerTokenInterceptor(
                        token_provider,
                        scheme=None,
                    ),
                ],
            ),
        )

        @self.client.post("/wx/{path}")
        async def query_messages(
            path: str = Path(),
            query_body: dict[str, Any] = Body(),
        ) -> dict[str, Any]:
            pass

        self.query_messages = query_messages

    async def close(self):
        await self.client.close()


class TelegramExecutor:
    def __init__(self, config: TelegramConfig):
        self.config = config
        self.sender_path = config.sender_path
        self.chat_path = config.chat_path

        self.login_api = TelegramLoginApi(config)
        self.token_provider = CallableTokenProvider(self._login)
        self.message_api = TelegramMessageApi(config, self.token_provider)

    async def _login(self) -> str:
        res = await self.login_api.login(
            name=self.config.username,
            password=self.config.password,
        )
        token = res.get("data")

        if not token:
            raise RuntimeError("登录失败，响应中没有 token")

        return token

    async def _get_sender_msg(
        self,
        sender_id: str,
        start_timestamp: int | None = None,
        end_timestamp: int | None = None,
        query_types: list[QueryType] | None = None,
        limit: LimitInt = 3000,
    ) -> list[ChatMessage]:
        query_body = self._build_query_body(
            query_types=query_types or ["txt"],
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            limit=limit,
            accountname=sender_id,
        )

        res = await self.message_api.query_messages(
            path=self.sender_path,
            query_body=query_body,
        )
        return self._decode_messages(res.get("datas", []), sender_id=sender_id)

    async def _get_chat_msg(
        self,
        chat_id: str,
        start_timestamp: int | None = None,
        end_timestamp: int | None = None,
        query_types: list[QueryType] | None = None,
        limit: LimitInt = 3000,
    ) -> list[ChatMessage]:
        query_body = self._build_query_body(
            query_types=query_types or ["txt"],
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            limit=limit,
            groupid=chat_id,
        )

        res = await self.message_api.query_messages(
            path=self.chat_path,
            query_body=query_body,
        )
        return self._decode_messages(res.get("datas", []), chat_id=chat_id)

    async def _get_all_msg_in_time_range(
        self,
        target_id: str,
        start_timestamp: int,
        end_timestamp: int,
        query_types: list[QueryType] | None = None,
        batch_limit: int = 3000,
        limit: int | None = None,
        target_type: TargetType = "sender",
    ) -> list[ChatMessage]:
        limit = limit or -1
        batch_limit = min(batch_limit, 5000)
        all_msg: list[ChatMessage] = []
        last_fetched_count = batch_limit

        while last_fetched_count == batch_limit:
            if target_type == "sender":
                batch_data = await self._get_sender_msg(
                    sender_id=target_id,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                    query_types=query_types,
                    limit=batch_limit,
                )
            else:
                batch_data = await self._get_chat_msg(
                    chat_id=target_id,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                    query_types=query_types,
                    limit=batch_limit,
                )

            last_fetched_count = len(batch_data)

            if not batch_data:
                break

            all_msg.extend(batch_data)

            if limit > 0 and len(all_msg) >= limit:
                return all_msg[:limit]

            end_timestamp = int(batch_data[-1].send_time.timestamp())

        return all_msg

    async def get_sender_msg(
        self,
        sender_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        query_types: list[QueryType] | None = None,
        limit: int | None = None,
    ) -> list[ChatMessage]:
        start_time = start_time or datetime.now() - timedelta(days=6 * 30)
        end_time = end_time or datetime.now()

        if limit is None or limit > 5000:
            return await self._get_all_msg_in_time_range(
                target_id=sender_id,
                start_timestamp=int(start_time.timestamp()),
                end_timestamp=int(end_time.timestamp()),
                query_types=query_types,
                limit=limit,
                target_type="sender",
            )

        if limit <= 0:
            return []

        return await self._get_sender_msg(
            sender_id=sender_id,
            start_timestamp=int(start_time.timestamp()),
            end_timestamp=int(end_time.timestamp()),
            query_types=query_types,
            limit=limit,
        )

    async def get_chat_msg(
        self,
        chat_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        query_types: list[QueryType] | None = None,
        limit: int | None = None,
    ) -> list[ChatMessage]:
        start_time = start_time or datetime.now() - timedelta(days=6 * 30)
        end_time = end_time or datetime.now()

        if limit is None or limit > 5000:
            return await self._get_all_msg_in_time_range(
                target_id=chat_id,
                start_timestamp=int(start_time.timestamp()),
                end_timestamp=int(end_time.timestamp()),
                query_types=query_types,
                limit=limit,
                target_type="chat",
            )

        if limit <= 0:
            return []

        return await self._get_chat_msg(
            chat_id=chat_id,
            start_timestamp=int(start_time.timestamp()),
            end_timestamp=int(end_time.timestamp()),
            query_types=query_types,
            limit=limit,
        )

    async def close(self):
        await self.message_api.close()
        await self.login_api.close()

    @staticmethod
    def _build_query_body(
        *,
        query_types: list[QueryType],
        start_timestamp: int | None,
        end_timestamp: int | None,
        limit: int,
        **target: str,
    ) -> dict[str, Any]:
        return {
            "apptype": "1030036",
            "opid": str(uuid.uuid4()),
            "param": {
                "type": query_types,
                "begintime": str(start_timestamp),
                "endtime": str(end_timestamp),
                "retrunnum": limit,
                **target,
            },
        }

    @staticmethod
    def _decode_messages(
        items: list[dict[str, Any]],
        *,
        sender_id: str | None = None,
        chat_id: str | None = None,
    ) -> list[ChatMessage]:
        return [
            ChatMessage(
                message_id=item.get("MD_ID"),
                chat_id=chat_id or item.get("GROUPID"),
                sender_id=sender_id or item.get("ACCOUNTNAME"),
                content=item.get("CONTENT"),
                send_time=datetime.fromtimestamp(int(item.get("MESSAGE_TIME", 0))),
                message_type=_DECODE_MESSAGE_TYPE.get(str(item.get("MSGTYPE"))),
            )
            for item in items
        ]


async def main():
    config = TelegramConfig(
        base_url="http://telegram-api.local",
        username="admin",
        password="password",
        sender_path="sender/messages",
        chat_path="chat/messages",
        verify_ssl=False,
    )
    executor = TelegramExecutor(config)

    # messages = await executor.get_sender_msg("sender-id", limit=100)
    # print(messages)

    await executor.close()


if __name__ == "__main__":
    asyncio.run(main())
