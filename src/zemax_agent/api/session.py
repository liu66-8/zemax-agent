import logging
from typing import Optional

from .connection import ConnectionMode, ZemaxConnection

logger = logging.getLogger(__name__)


class ZemaxSession:
    """
    Zemax 会话管理器
    管理连接生命周期，支持连接池模式
    """

    def __init__(self):
        self._connection: Optional[ZemaxConnection] = None

    @property
    def connection(self) -> Optional[ZemaxConnection]:
        return self._connection

    @property
    def is_active(self) -> bool:
        return self._connection is not None and self._connection.is_connected

    def open(
        self,
        mode: ConnectionMode = ConnectionMode.STANDALONE,
        timeout: float = 30.0,
    ) -> ZemaxConnection:
        """开启新会话"""
        if self._connection is not None:
            logger.warning("已有活跃连接，将先关闭旧连接")
            self.close()

        self._connection = ZemaxConnection(mode=mode, timeout=timeout)
        self._connection.connect()
        return self._connection

    def close(self) -> None:
        """关闭当前会话"""
        if self._connection is not None:
            self._connection.disconnect()
            self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
