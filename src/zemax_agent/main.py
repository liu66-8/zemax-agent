import sys
from pathlib import Path

from zemax_agent.core import load_config, setup_logging, get_config


def main():
    project_root = Path(__file__).parent.parent
    config_path = project_root / "config.yaml"

    config = load_config(str(config_path))
    logger = setup_logging(
        level=config.logging.level,
        log_file=config.logging.file,
        fmt=config.logging.format,
        datefmt=config.logging.date_format,
    )

    logger.info("Zemax Agent starting...")
    logger.info("LLM provider: %s, model: %s", config.llm.provider, config.llm.model)
    logger.info("ZOS connection mode: %s", config.zos.connection_mode)
    logger.info("Workspace: %s", config.project.workspace_dir)

    logger.info("Zemax Agent ready. Waiting for Tauri connection...")


if __name__ == "__main__":
    main()
