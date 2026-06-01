import json
import logging
import sys
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

from zemax_agent.core import load_config, setup_logging, get_config

logger = logging.getLogger(__name__)

# ── ZOS-API initialization ──
_ZOS_INITIALIZED = False
_ZOS_DIR = ""


def _init_zos_api() -> bool:
    global _ZOS_INITIALIZED, _ZOS_DIR
    if _ZOS_INITIALIZED:
        return True
    try:
        import clr
        # Try the known installation path
        candidate = r"C:\Program Files\ANSYS Inc\Ansys Zemax OpticStudio 2024 R1.00\ZOS-API\Libraries"
        import os
        if not os.path.isdir(candidate):
            return False
        sys.path.append(candidate)
        clr.AddReference("ZOSAPI_NetHelper")
        from ZOSAPI_NetHelper import ZOSAPI_Initializer
        _ZOS_DIR = ZOSAPI_Initializer.GetZemaxDirectory()
        ZOSAPI_Initializer.Initialize()
        _ZOS_INITIALIZED = True
        logger.info("ZOS-API initialized. Zemax dir: %s", _ZOS_DIR)
        return True
    except Exception as e:
        logger.debug("ZOS-API init failed: %s", e)
        return False

# ── ZOS tool definitions (OpenAI function-calling format) ──
ZOS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "zos.get_system_info",
            "description": "获取当前 OpticStudio 系统信息(EFL, F/#, NA, 面数等)",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos.load_zmx",
            "description": "从指定路径加载 ZMX 设计文件",
            "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "ZMX 文件路径"}}, "required": ["path"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos.set_aperture",
            "description": "设置系统孔径类型和值",
            "parameters": {"type": "object", "properties": {"aperture_type": {"type": "string", "enum": ["EPD", "FNumber", "NA"]}, "value": {"type": "number"}}, "required": ["aperture_type", "value"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos.set_fields",
            "description": "设置视场配置",
            "parameters": {"type": "object", "properties": {"fields": {"type": "array", "items": {"type": "object", "properties": {"x": {"type": "number"}, "y": {"type": "number"}}}}}, "required": ["fields"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos.set_wavelengths",
            "description": "设置波长配置(单位: 微米)",
            "parameters": {"type": "object", "properties": {"wavelengths": {"type": "array", "items": {"type": "number"}}, "primary_index": {"type": "integer", "default": 1}}, "required": ["wavelengths"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos.insert_surface",
            "description": "在指定位置后插入新面",
            "parameters": {"type": "object", "properties": {"surface_index": {"type": "integer"}, "surface_type": {"type": "string", "default": "Standard"}, "radius": {"type": "number", "default": 0}, "thickness": {"type": "number", "default": 10}, "glass": {"type": "string", "default": ""}}, "required": ["surface_index"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos.set_surface_data",
            "description": "修改指定面的参数(曲率半径/厚度/玻璃/面型/光阑)",
            "parameters": {"type": "object", "properties": {"surface_index": {"type": "integer"}, "radius": {"type": "number"}, "thickness": {"type": "number"}, "glass": {"type": "string"}, "surface_type": {"type": "string"}, "is_stop": {"type": "boolean"}}, "required": ["surface_index"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos.get_lens_summary",
            "description": "获取镜头完整摘要(所有面数据+EFL+F/#+总长)",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos.get_mtf",
            "description": "运行 MTF 分析并返回结果",
            "parameters": {"type": "object", "properties": {"frequency": {"type": "number", "default": 30, "description": "MTF 频率(lp/mm)"}}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos.get_spot",
            "description": "运行点列图分析并返回 RMS/几何半径",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos.get_seidel",
            "description": "运行赛德尔像差分析(球差/彗差/像散/场曲/畸变/色差)",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos.get_wavefront",
            "description": "运行波前分析并返回 RMS 和 PV 值",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos.run_optimization",
            "description": "运行局部优化并返回结果(初始MF/最终MF/改善率)",
            "parameters": {"type": "object", "properties": {"cycles": {"type": "integer", "default": 50}}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos.create_cooke_triplet",
            "description": "自动创建 Cooke Triplet 初始结构(三片式经典设计)",
            "parameters": {"type": "object", "properties": {"focal_length": {"type": "number", "default": 100}, "f_number": {"type": "number", "default": 4}, "field_angle": {"type": "number", "default": 20}}, "required": ["focal_length"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos.create_doublet",
            "description": "创建双胶合透镜初始结构(正透镜+负透镜胶合, 校正球差和色差). 需要 OpticStudio 运行.",
            "parameters": {"type": "object", "properties": {"focal_length": {"type": "number", "default": 100, "description": "有效焦距(mm)"}, "f_number": {"type": "number", "default": 5, "description": "F数"}, "glass_crown": {"type": "string", "default": "N-BK7", "description": "冕牌玻璃"}, "glass_flint": {"type": "string", "default": "F2", "description": "火石玻璃"}, "field_angle": {"type": "number", "default": 1, "description": "半视场角(度)"}}, "required": ["focal_length"]},
        },
    },
]

# ── Tool execution handler ──
def execute_tool(tool_name: str, params: dict) -> dict:
    if not _init_zos_api():
        return {"success": False, "error": "Zemax OpticStudio 2024 R1 未检测到。请确认 ZOS-API 已安装。", "source": "zos-api"}
    try:
        from zemax_agent.zos import ZOSDispatcher
        dispatcher = ZOSDispatcher.get_instance()
        if not dispatcher.is_connected:
            dispatcher.connect(timeout=15)
        result = dispatcher.submit_and_wait(tool_name, params=params, timeout=30)
        return {"success": True, "data": result, "source": "zos-api"}
    except Exception as e:
        logger.warning("ZOS tool failed: %s - %s", tool_name, e)
        return {"success": False, "error": f"执行失败: {str(e)}", "source": "zos-api"}


class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/health":
            self._json({"status": "ok", "zos": self._check_zos(), "qdrant": False, "python": True})
        elif self.path == "/api/health/zos":
            ok = self._check_zos()
            self._json({"connected": ok, "message": "OpticStudio detected" if ok else "OpticStudio not available"})
        elif self.path == "/api/health/qdrant":
            self._json({"connected": False, "message": "Qdrant not running"})
        elif self.path == "/api/zos/tools":
            self._json(ZOS_TOOLS)
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}

        if self.path == "/api/zos/execute":
            tool_name = body.get("tool", "")
            params = body.get("params", {})
            if not tool_name:
                self._json({"success": False, "error": "Missing tool name"})
                return
            logger.info("Executing tool: %s(%s)", tool_name, json.dumps(params))
            result = execute_tool(tool_name, params)
            self._json(result)
        elif self.path == "/api/projects":
            self._json([])
        elif self.path == "/api/tasks":
            self._json([])
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _check_zos(self) -> bool:
        return _init_zos_api()

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def log_message(self, format, *args):
        pass


def run_server(port: int = 9876):
    server = HTTPServer(("127.0.0.1", port), APIHandler)
    logger.info("API server on http://127.0.0.1:%d", port)
    server.serve_forever()


def main():
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.yaml"
    config = load_config(str(config_path))
    logger = setup_logging(level=config.logging.level, log_file=config.logging.file, fmt=config.logging.format, datefmt=config.logging.date_format)
    logger.info("Zemax Agent starting...")
    logger.info("LLM: %s / %s", config.llm.provider, config.llm.model)
    logger.info("ZOS mode: %s | Workspace: %s", config.zos.connection_mode, config.project.workspace_dir)

    t = threading.Thread(target=run_server, args=(9876,), daemon=True)
    t.start()
    logger.info("Ready. API: http://127.0.0.1:9876 | Tools: %d registered", len(ZOS_TOOLS))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == "__main__":
    main()
