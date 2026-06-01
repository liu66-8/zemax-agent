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

# ── Config & State ──
_CONFIG = None

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
            "name": "zos_get_system_info",
            "description": "获取当前 OpticStudio 系统信息(EFL, F/#, NA, 面数等)",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos_load_zmx",
            "description": "从指定路径加载 ZMX 设计文件",
            "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "ZMX 文件路径"}}, "required": ["path"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos_set_aperture",
            "description": "设置系统孔径类型和值",
            "parameters": {"type": "object", "properties": {"aperture_type": {"type": "string", "enum": ["EPD", "FNumber", "NA"]}, "value": {"type": "number"}}, "required": ["aperture_type", "value"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos_set_fields",
            "description": "设置视场配置",
            "parameters": {"type": "object", "properties": {"fields": {"type": "array", "items": {"type": "object", "properties": {"x": {"type": "number"}, "y": {"type": "number"}}}}}, "required": ["fields"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos_set_wavelengths",
            "description": "设置波长配置(单位: 微米)",
            "parameters": {"type": "object", "properties": {"wavelengths": {"type": "array", "items": {"type": "number"}}, "primary_index": {"type": "integer", "default": 1}}, "required": ["wavelengths"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos_insert_surface",
            "description": "在指定位置后插入新面",
            "parameters": {"type": "object", "properties": {"surface_index": {"type": "integer"}, "surface_type": {"type": "string", "default": "Standard"}, "radius": {"type": "number", "default": 0}, "thickness": {"type": "number", "default": 10}, "glass": {"type": "string", "default": ""}}, "required": ["surface_index"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos_set_surface_data",
            "description": "修改指定面的参数(曲率半径/厚度/玻璃/面型/光阑)",
            "parameters": {"type": "object", "properties": {"surface_index": {"type": "integer"}, "radius": {"type": "number"}, "thickness": {"type": "number"}, "glass": {"type": "string"}, "surface_type": {"type": "string"}, "is_stop": {"type": "boolean"}}, "required": ["surface_index"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos_get_lens_summary",
            "description": "获取镜头完整摘要(所有面数据+EFL+F/#+总长)",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos_get_mtf",
            "description": "运行 MTF 分析并返回结果",
            "parameters": {"type": "object", "properties": {"frequency": {"type": "number", "default": 30, "description": "MTF 频率(lp/mm)"}}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos_get_spot",
            "description": "运行点列图分析并返回 RMS/几何半径",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos_get_seidel",
            "description": "运行赛德尔像差分析(球差/彗差/像散/场曲/畸变/色差)",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos_get_wavefront",
            "description": "运行波前分析并返回 RMS 和 PV 值",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos_run_optimization",
            "description": "运行局部优化并返回结果(初始MF/最终MF/改善率)",
            "parameters": {"type": "object", "properties": {"cycles": {"type": "integer", "default": 50}}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos_create_cooke_triplet",
            "description": "自动创建 Cooke Triplet 初始结构(三片式经典设计)",
            "parameters": {"type": "object", "properties": {"focal_length": {"type": "number", "default": 100}, "f_number": {"type": "number", "default": 4}, "field_angle": {"type": "number", "default": 20}}, "required": ["focal_length"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "zos_create_doublet",
            "description": "创建双胶合透镜初始结构(正透镜+负透镜胶合, 校正球差和色差). 需要 OpticStudio 运行.",
            "parameters": {"type": "object", "properties": {"focal_length": {"type": "number", "default": 100, "description": "有效焦距(mm)"}, "f_number": {"type": "number", "default": 5, "description": "F数"}, "glass_crown": {"type": "string", "default": "N-BK7", "description": "冕牌玻璃"}, "glass_flint": {"type": "string", "default": "F2", "description": "火石玻璃"}, "field_angle": {"type": "number", "default": 1, "description": "半视场角(度)"}}, "required": ["focal_length"]},
        },
    },
]

# ── ZOS connection singleton ──
_connection = None


def _get_connection():
    global _connection
    if _connection is None:
        import sys, os
        zos_root = r"C:\Program Files\ANSYS Inc\Ansys Zemax OpticStudio 2024 R1.00"
        zos_libs = os.path.join(zos_root, "ZOS-API", "Libraries")
        for p in (zos_root, zos_libs):
            if os.path.isdir(p) and p not in sys.path:
                sys.path.append(p)
        from zemax_agent.zos.connection import ZOSConnection
        _connection = ZOSConnection()
    if not _connection.is_connected:
        _connection.connect(timeout=15)
    return _connection


# ── Tool execution handler ──
def execute_tool(tool_name: str, params: dict) -> dict:
    if not _init_zos_api():
        return {"success": False, "error": "Zemax OpticStudio 2024 R1 未检测到。请确认 ZOS-API 已安装。", "source": "zos-api"}
    try:
        internal = tool_name.replace("zos_", "zos.", 1)
        short = internal.replace("zos.", "")
        conn = _get_connection()

        if short == "get_system_info":
            from zemax_agent.zos.api_system import get_system_info
            data = get_system_info(conn)
            return {"success": True, "data": data.model_dump() if hasattr(data, 'model_dump') else str(data), "source": "zos-api"}

        if short == "get_lens_summary":
            from zemax_agent.zos.api_lens import get_lens_data_summary
            data = get_lens_data_summary(conn)
            return {"success": True, "data": data.model_dump() if hasattr(data, 'model_dump') else str(data), "source": "zos-api"}

        if short == "load_zmx":
            from zemax_agent.zos.api_system import load_zmx
            data = load_zmx(conn, params.get("path", ""))
            return {"success": True, "data": data.model_dump() if hasattr(data, 'model_dump') else str(data), "source": "zos-api"}

        if short == "set_aperture":
            from zemax_agent.zos.api_lens import set_aperture
            set_aperture(conn, params["aperture_type"], float(params["value"]))
            return {"success": True, "data": {"aperture": params}, "source": "zos-api"}

        if short == "set_fields":
            from zemax_agent.zos.api_lens import set_fields
            from zemax_agent.zos.models import FieldConfig
            fields_list = [(f["x"], f["y"]) for f in params["fields"]]
            cfg = FieldConfig(field_count=len(fields_list), field_type=0, fields=fields_list)
            set_fields(conn, cfg)
            return {"success": True, "data": {"fields": params["fields"]}, "source": "zos-api"}

        if short == "set_wavelengths":
            from zemax_agent.zos.api_lens import set_wavelengths
            from zemax_agent.zos.models import WavelengthConfig
            wls = params["wavelengths"]
            cfg = WavelengthConfig(wavelength_count=len(wls), wavelengths=wls, primary_wavelength=params.get("primary_index", 2))
            set_wavelengths(conn, cfg)
            return {"success": True, "data": {"wavelengths": wls}, "source": "zos-api"}

        if short == "insert_surface":
            from zemax_agent.zos.api_lens import insert_surface, set_surface_data
            data = insert_surface(conn, int(params["surface_index"]))
            extra = {k: v for k, v in params.items() if k != "surface_index" and v}
            if extra:
                set_surface_data(conn, data.index, **extra)
            return {"success": True, "data": data.model_dump() if hasattr(data, 'model_dump') else str(data), "source": "zos-api"}

        if short == "set_surface_data":
            from zemax_agent.zos.api_lens import set_surface_data
            idx = int(params.pop("surface_index"))
            data = set_surface_data(conn, idx, **params)
            return {"success": True, "data": data.model_dump() if hasattr(data, 'model_dump') else str(data), "source": "zos-api"}

        if short == "get_mtf":
            from zemax_agent.zos.api_analysis import get_mtf
            freq = float(params.get("frequency", 30))
            data = get_mtf(conn, freq)
            return {"success": True, "data": data.model_dump() if hasattr(data, 'model_dump') else str(data), "source": "zos-api"}

        if short == "get_spot":
            from zemax_agent.zos.api_analysis import get_spot
            data = get_spot(conn)
            return {"success": True, "data": data.model_dump() if hasattr(data, 'model_dump') else str(data), "source": "zos-api"}

        if short == "get_seidel":
            from zemax_agent.zos.api_analysis import get_seidel
            data = get_seidel(conn)
            return {"success": True, "data": data.model_dump() if hasattr(data, 'model_dump') else str(data), "source": "zos-api"}

        if short == "get_wavefront":
            from zemax_agent.zos.api_analysis import get_wavefront
            data = get_wavefront(conn)
            return {"success": True, "data": data.model_dump() if hasattr(data, 'model_dump') else str(data), "source": "zos-api"}

        if short == "run_optimization":
            from zemax_agent.zos.api_optimize import build_merit_function, run_optimization
            build_merit_function(conn, clear_existing=True)
            cycles = int(params.get("cycles", 50))
            data = run_optimization(conn, cycles=cycles)
            return {"success": True, "data": data.model_dump() if hasattr(data, 'model_dump') else str(data), "source": "zos-api"}

        if short in ("create_cooke_triplet", "create_doublet"):
            return _create_design(conn, short, params)

        return {"success": False, "error": f"Unknown tool: {tool_name}", "source": "zos-api"}

    except Exception as e:
        logger.warning("Tool %s failed: %s", tool_name, e)
        import traceback
        logger.warning("Traceback: %s", traceback.format_exc())
        return {"success": False, "error": f"{str(e)}", "source": "zos-api"}


def _create_design(conn, design_type: str, params: dict) -> dict:
    from zemax_agent.zos.api_system import make_sequential, get_system_info
    from zemax_agent.zos.api_lens import (
        set_aperture, set_fields, set_wavelengths,
        insert_surface, set_surface_data, get_lens_data_summary,
    )
    from zemax_agent.zos.models import FieldConfig, WavelengthConfig

    make_sequential(conn)
    fl = float(params.get("focal_length", 100))
    fn = float(params.get("f_number", 5))
    fov = float(params.get("field_angle", 1))
    gc = params.get("glass_crown", "N-BK7")
    gf = params.get("glass_flint", "F2")

    set_aperture(conn, "FNumber", fn)
    set_fields(conn, FieldConfig(
        field_count=3, field_type=0,
        fields=[(0, 0.0), (0, 0.7*fov), (0, fov)],
    ))
    set_wavelengths(conn, WavelengthConfig(wavelength_count=3, wavelengths=[0.486, 0.587, 0.656], primary_wavelength=2))

    # Build doublet: OBJ → Lens1_front → Lens1_Lens2_cement → Lens2_back → IMG
    insert_surface(conn, 0)  # Surface 1: first lens
    insert_surface(conn, 1)  # Surface 2: cement
    insert_surface(conn, 2)  # Surface 3: second lens back

    if design_type == "create_doublet":
        set_surface_data(conn, 1, surface_type="Standard", radius=0.45*fl, thickness=0.08*fl, glass=gc)
        set_surface_data(conn, 2, surface_type="Standard", radius=-0.35*fl, thickness=0.02*fl, glass=gf)
        set_surface_data(conn, 3, surface_type="Standard", radius=-1.2*fl, thickness=0.8*fl, glass="")
        set_surface_data(conn, 2, is_stop=True)
    else:
        # create_cooke_triplet
        insert_surface(conn, 3)
        insert_surface(conn, 4)
        set_surface_data(conn, 1, surface_type="Standard", radius=0.45*fl, thickness=0.05*fl, glass="N-BK7")
        set_surface_data(conn, 2, surface_type="Standard", radius=-2.5*fl, thickness=0.3*fl, glass="", is_stop=True)
        set_surface_data(conn, 3, surface_type="Standard", radius=-0.4*fl, thickness=0.03*fl, glass="SF5")
        set_surface_data(conn, 4, surface_type="Standard", radius=1.5*fl, thickness=0.08*fl, glass="")
        set_surface_data(conn, 5, surface_type="Standard", radius=0.55*fl, thickness=0.05*fl, glass="N-BK7")
        set_surface_data(conn, 6, surface_type="Standard", radius=-1.2*fl, thickness=0.42*fl, glass="")

    summary = get_lens_data_summary(conn)

    # Auto-save ZMX to workspace
    try:
        import os, time
        from zemax_agent.zos.api_system import save_zmx
        ws = os.path.abspath(_CONFIG.project.workspace_dir) if _CONFIG else os.path.abspath("./workspace")
        os.makedirs(ws, exist_ok=True)
        fname = f"doublet_{design_type}_{int(time.time())}.zmx"
        save_zmx(conn, os.path.join(ws, fname))
        logger.info("Auto-saved ZMX: %s", fname)
    except Exception as e:
        logger.warning("Auto-save ZMX failed: %s", e)

    return {"success": True, "data": summary.model_dump() if hasattr(summary, 'model_dump') else str(summary), "source": "zos-api"}


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
        elif self.path == "/api/settings":
            cfg = _CONFIG
            if cfg:
                self._json({
                    "llmApiKey": cfg.llm.api_key,
                    "llmApiBase": cfg.llm.api_base,
                    "llmModel": cfg.llm.model,
                    "llmProvider": cfg.llm.provider,
                    "zosMode": cfg.zos.connection_mode,
                    "zosTimeout": cfg.zos.connection_timeout,
                    "qdrantUrl": cfg.storage.qdrant_url,
                    "workspaceDir": cfg.project.workspace_dir,
                })
            else:
                self._json({"error": "config not loaded"}, 503)
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
        self.wfile.write(json.dumps(data, ensure_ascii=False, allow_nan=False).encode())

    def log_message(self, format, *args):
        pass


def run_server(port: int = 9876):
    server = HTTPServer(("127.0.0.1", port), APIHandler)
    logger.info("API server on http://127.0.0.1:%d", port)
    server.serve_forever()


def main():
    global _CONFIG
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.yaml"
    _CONFIG = load_config(str(config_path))
    config = _CONFIG
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
