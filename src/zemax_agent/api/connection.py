import logging
import time
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ConnectionMode(Enum):
    STANDALONE = "standalone"
    EXTENSION = "extension"


class ZemaxConnection:
    """
    Zemax OpticStudio ZOS-API 连接管理器

    支持 Standalone 模式（新建Zemax实例）和 Extension 模式（附着到已运行的Zemax）
    提供自动重连、连接状态检测和超时管理功能
    """

    def __init__(
        self,
        mode: ConnectionMode = ConnectionMode.STANDALONE,
        timeout: float = 30.0,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 3,
    ):
        self.mode = mode
        self.timeout = timeout
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self._zosapi: Any = None
        self._zosapi_app: Any = None
        self._the_system: Any = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """检测是否已连接到 Zemax"""
        if not self._connected:
            return False
        try:
            _ = self._zosapi_app
            return True
        except Exception:
            self._connected = False
            return False

    @property
    def zosapi(self) -> Any:
        """获取 ZOSAPI 根对象"""
        if not self._connected:
            raise ConnectionError("未连接到 Zemax")
        return self._zosapi

    @property
    def app(self) -> Any:
        """获取 Zemax 应用对象"""
        if not self._connected:
            raise ConnectionError("未连接到 Zemax")
        return self._zosapi_app

    @property
    def system(self) -> Any:
        """获取当前光学系统对象"""
        if not self._connected:
            raise ConnectionError("未连接到 Zemax")
        return self._the_system

    def connect(self) -> bool:
        """
        建立与 Zemax 的连接

        Returns:
            bool: 连接成功返回 True

        Raises:
            ConnectionError: 连接失败
            ImportError: ZOS-API DLL 未找到
        """
        logger.info(f"正在以 {self.mode.value} 模式连接 Zemax...")

        try:
            import os

            import clr  # pythonnet

            zemax_path = os.environ.get(
                "ZEMAX_PATH", r"C:\Program Files\Ansys Zemax OpticStudio"
            )

            dll_path = os.path.join(zemax_path, "ZOSAPI_NetHelper.dll")
            if not os.path.exists(dll_path):
                raise ImportError(
                    f"未找到 ZOSAPI_NetHelper.dll，请设置 ZEMAX_PATH 环境变量。"
                    f"当前路径: {dll_path}"
                )

            clr.AddReference(dll_path)
            import ZOSAPI_NetHelper

            if self.mode == ConnectionMode.STANDALONE:
                success, self._zosapi, message = (
                    ZOSAPI_NetHelper.ZOSAPI_Initializer.InitializeWithTimeout(
                        self.timeout
                    )
                )
            else:
                success, self._zosapi, message = (
                    ZOSAPI_NetHelper.ZOSAPI_Initializer.InitializeInExtensionMode(
                        self.timeout
                    )
                )

            if not success:
                raise ConnectionError(f"Zemax 连接初始化失败: {message}")

            self._zosapi_app = self._zosapi.CreateNewApplication()
            if self._zosapi_app is None:
                raise ConnectionError("无法创建 Zemax 应用实例")

            self._the_system = self._zosapi_app.PrimarySystem
            if self._the_system is None:
                raise ConnectionError("无法获取主光学系统")

            self._connected = True
            logger.info(f"Zemax 连接成功 (模式: {self.mode.value})")
            return True

        except ImportError as e:
            logger.error(f"ZOS-API 导入失败: {e}")
            raise
        except Exception as e:
            logger.error(f"Zemax 连接失败: {e}")
            self._connected = False
            raise ConnectionError(f"连接 Zemax 失败: {e}") from e

    def disconnect(self) -> None:
        """断开与 Zemax 的连接并释放资源"""
        logger.info("正在断开 Zemax 连接...")
        try:
            if self._zosapi_app is not None:
                self._zosapi_app.CloseApplication()
        except Exception as e:
            logger.warning(f"关闭 Zemax 应用时出现异常: {e}")
        finally:
            self._zosapi = None
            self._zosapi_app = None
            self._the_system = None
            self._connected = False
            logger.info("Zemax 连接已断开")

    def reconnect(self) -> bool:
        """
        重新连接 Zemax

        Returns:
            bool: 重连成功返回 True
        """
        logger.info("尝试重新连接 Zemax...")
        self.disconnect()
        time.sleep(1.0)
        return self.connect()

    def ensure_connected(self) -> None:
        """确保当前处于连接状态，如断开则自动重连"""
        if not self.is_connected:
            if not self.auto_reconnect:
                raise ConnectionError("Zemax 连接已断开，自动重连已禁用")
            logger.warning("Zemax 连接断开，尝试自动重连...")
            for attempt in range(1, self.max_reconnect_attempts + 1):
                try:
                    if self.reconnect():
                        logger.info(f"自动重连成功 (第 {attempt} 次尝试)")
                        return
                except Exception as e:
                    logger.warning(
                        f"自动重连失败 (第 {attempt}/{self.max_reconnect_attempts} 次): {e}"
                    )
                    if attempt < self.max_reconnect_attempts:
                        wait_time = 2**attempt
                        time.sleep(wait_time)
            raise ConnectionError(
                f"自动重连失败，已尝试 {self.max_reconnect_attempts} 次"
            )

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
