import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import lsprotocol.converters as lsp_con
import lsprotocol.types as lsp_types
import pylsp.config.config as pylsp_conf
import pylsp.lsp as pylsp_lsp
import pylsp.workspace as pylsp_ws
import pyre_check.client.language_server.protocol as pyre_proto
from pylsp import hookimpl

logger: logging.Logger = logging.getLogger(__name__)
# A logging prefix.
PLUGIN: str = "[python-lsp-pyre]"


@hookimpl
def pylsp_settings(config: pylsp_conf.Config) -> Dict[str, Dict[str, Dict[str, bool]]]:
    """
    Default configuration for the plugin. Ensures all keys are set.
    """
    return {
        "plugins": {
            "pyre": {
                "enabled": True,
                "create-pyre-config": False,
            }
        }
    }


@hookimpl
def pylsp_lint(
    config: pylsp_conf.Config,
    workspace: pylsp_ws.Workspace,
    document: pylsp_ws.Document,
    is_saved: bool,
) -> List[Dict[str, Any]]:
    """
    Lints files (saved, not in-progress) and returns found problems.
    """
    logger.debug(f"Working with {document.path}, {is_saved=}")
    maybe_create_pyre_config(config=config, workspace=workspace)
    if is_saved:
        with workspace.report_progress("lint: pyre check", "running"):
            settings = config.plugin_settings("pyre")
            diagnostics = run_pyre(workspace=workspace, document=document, settings=settings)
        workspace.show_message(message=f"Pyre reported {len(diagnostics)} issue(s).")
        # Deal with location stuff by using unstructure() for now.
        return lsp_con.get_converter().unstructure(diagnostics)
    else:
        return []


def abend(message: str, workspace: pylsp_ws.Workspace) -> Dict[str, Any]:
    """
    Deals with exceptions that Pyre might throw via subprocess.

    Basically, make it visible in as many ways as possible - logging, workspace messaging, and
    actual lint results.
    """
    logger.exception(f"{PLUGIN} {message}")
    workspace.show_message(
        message=f"{PLUGIN} {message}", msg_type=pylsp_lsp.MessageType.Error
    )
    return {
        "source": "pyre",
        "severity": lsp_types.DiagnosticSeverity.Error,
        "code": "E999",
        "message": message,
        "range": pyre_proto.LspRange(
            start=pyre_proto.LspPosition(line=0, character=0),
            end=pyre_proto.LspPosition(line=0, character=1),
        ),
    }


def run_pyre(
    workspace: pylsp_ws.Workspace, document: pylsp_ws.Document, settings: Dict
) -> List[Dict[str, Any]]:
    """
    Calls Pyre, converts output to internal structs
    """
    try:
        data = really_run_pyre(root_path=workspace.root_path)
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
            }
            for x in data
            if document.path == f"{workspace.root_path}/{x['path']}"
        ]
    except subprocess.CalledProcessError as e:
        msg = f"ABEND: Pyre failed: {str(e)}. {e.stderr.decode('utf-8')}"
        checks = [abend(message=msg, workspace=workspace)]
    except Exception as e:
        msg = f"ABEND: Catchall {type(e)} - {str(e)}"
        checks = [abend(message=msg, workspace=workspace)]

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


def maybe_create_pyre_config(
    config: pylsp_conf.Config, workspace: pylsp_ws.Workspace
) -> None:
    """
    Initializes a .pyre_configuration file if `create-pyre-config` setting is enabled.

    Only initializes if the file is missing.
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
    try:
        if settings["create-pyre-config"]:
            docroot = workspace.root_path
            path = Path(docroot).joinpath(".pyre_configuration")
            if not path.exists():
                logger.info(f"Initializing {path}")
                with path.open(mode="w") as f:
                    f.write(json.dumps(default_config, indent=4))
                    f.write("\n")

    except KeyError:
        message = f"{PLUGIN} create-pyre-config setting not found in dictionary"
        logger.exception(message)
        workspace.show_message(message=message, msg_type=pylsp_lsp.MessageType.Warning)
