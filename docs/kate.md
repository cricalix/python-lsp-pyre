# Using Python LSP with Kate

## Poetry edition

If you're using Poetry to manage your Python virtualenvs, dependencies etcetera, then it's easiest to run the language server via poetry as well. This necessitates that every virtualenv has to be configured with `python-lsp-server`, `python-lsp-pyre`, and so on, but also means that each setup is independent of the others

In Settings > LSP Client > User Server Settings (normally found at `$USER/.config/kate/lspclient/settings.json`), the language server can be configured as

```json
{
  "servers": {
    "python": {
      "command": [
        "poetry",
        "run",
        "pylsp",
        "--check-parent-process",
        "--verbose",
        "--log-file",
        "/tmp/pylsp"
      ],
      "rootIndicationFileNames": [
        "poetry.lock",
        "pyproject.toml"
      ],
      "url": "https://github.com/python-lsp/python-lsp-server",
      "highlightingModeRegex": "^Python$"
    }
  }
}
```

This is very similar to the default Python LSP setup for Kate, just putting `poetry run` in front of the normal command.

If you want verbose debug logs, then add `, --verbose` after `--check-parent-process`; these will render in Kate's **Output** view.

If you wish to have a log file then add `, "--log-file", "/tmp/pylsp"` after `--check-parent-process`; change the log file path to suit.

The Python Language Server documentation supercedes the above instructions.

The **rootIndicationFileNames** entry is used to ensure that the correct root directory is passed to the language server on requests for linting etcetera, assuming that the project has a **pyproject.toml** file.

To pass [configuration options](Configuration.md) to the server, use the `settings` sub-key, splitting out each component of the key on the dot to make it a JSON structure key.

For example, `pylsp.plugins.pyre.create-pyre-config` would be converted to:

```json
{
  "servers": {
    "python": {
      "command": ["..."],
      "settings": {
        "pylsp": {
          "plugins": {
            "pyre": {
              "create-pyre-config": true
            }
          }
        }
      }
    }
  }
}
```
