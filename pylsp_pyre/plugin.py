import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import lsprotocol.converters as lsp_con
import lsprotocol.types as lsp_types
import pyre_check.client.language_server.protocol as pyre_proto
from pylsp import hookimpl
from pylsp.config.config import Config
from pylsp.workspace import Document, Workspace

logger: logging.Logger = logging.getLogger(__name__)


@hookimpl
def pylsp_settings() -> Dict[str, Dict[str, Dict[str, bool]]]:
    return {
        "plugins": {
            "pyre": {
                "enabled": True,
                "auto-config": True,
            }
        }
    }


@hookimpl
def pylsp_initialize(config: Config, workspace: Workspace) -> None:
    """
    Checks for a Pyre configuration existence.

    Runs on plugin init, relies on the workspace document root to know where to look for
    the config file.
    """
    default_config = json.loads(
        """
        {
      "site_package_search_strategy": "all",
      "source_directories": [
        "."
      ],
      "exclude": [
        "\/setup.py",
        ".*\/build\/.*"
      ]
    }
    """
    )
    settings = config.plugin_settings("pyre")
    if settings["auto-config"]:
        docroot = workspace.root_path
        path = Path(docroot).joinpath(".pyre_configuration")
        if not path.exists():
            logger.info(f"Initializing {path}")
            with path.open(mode="w") as f:
                f.write(json.dumps(default_config, indent=4))
                f.write("\n")


@hookimpl
def pylsp_lint(
    config: Config, workspace: Workspace, document: Document, is_saved: bool
) -> List[Dict[str, Any]]:
    """
    Lints files (saved, not in-progress) and returns found problems.
    """
    logger.debug(f"Working with {document.path}, {is_saved=}")
    if is_saved:
        with workspace.report_progress("lint: pyre check", "running"):
            settings = config.plugin_settings("pyre")
            diagnostics = run_pyre(
                root_path=workspace.root_path, document=document, settings=settings
            )
        workspace.show_message(message=f"Pyre reported {len(diagnostics)} issue(s).")
        # Deal with location stuff by using unstructure() for now.
        return lsp_con.get_converter().unstructure(diagnostics)
    else:
        return []


def add_pyre_config(root_path: str) -> None:
    """
        {
      "site_package_search_strategy": "all",
      "source_directories": [
        "."
      ],
      "exclude": [
        "\/setup.py",
        ".*\/build\/.*"
      ]
    }
    """


def run_pyre(root_path: str, document: Document, settings: Dict) -> List[Dict[str, Any]]:
    """
    Calls Pyre, converts output to internal structs
    """
    try:
        data = really_run_pyre(root_path=root_path)
        data = json.loads(data.decode("utf-8"))
        checks = [
            {
                "source": "pyre",
                "severity": lsp_types.DiagnosticSeverity.Error,
                "code": x["code"],
                "message": x["long_description"],
                "range": pyre_proto.LspRange(
                    start=pyre_proto.LspPosition(line=(x["line"] - 1), character=x["column"]),
                    end=pyre_proto.LspPosition(
                        line=(x["stop_line"] - 1), character=x["stop_column"]
                    ),
                ),
                # "filename": x["path"],
            }
            for x in data
            if document.path == f"{root_path}/{x['path']}"
        ]
    except Exception as e:
        logger.exception(f"ABEND: Pyre call raised {type(e)} - {str(e)}")
        checks = []

    return checks


def really_run_pyre(root_path: str) -> bytes:
    """
    Runs pyre directly via subprocess.

    Pyre has a language server mode, but it's easier to just get the binary to run instead,
    and avoid any need for watchman.
    """
    logger.debug(f"Running pyre at {root_path=}")
    try:
        return subprocess.run(
            args=["pyre", "--output", "json", "check"],
            capture_output=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError as e:
        # If there are no typing errors, pyre exits with returncode 0
        # If there are typing errors, pyre exits with returncode 1
        # If there are configuration errors, pyre exits with returncode 6
        if e.returncode in (0, 1):
            return e.output
        raise
