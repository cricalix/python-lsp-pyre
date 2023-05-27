# python-lsp-pyre

This is a plugin for the [Python LSP Server](https://github.com/python-lsp/python-lsp-server).

It implements support for calling Meta's [Pyre type checker](https://github.com/facebook/pyre-check) via a subprocess.

Pyre does offer a language server of its own, and that may be more useful to you if your editor supports multiple language servers per language.

## Features

This plugin adds the following features to `python-lsp-server`:

- Type linting via Meta's Pyre (pyre-check)

## Installation

To use this plugin, you need to install this plugin in the same virtualenv as `python-lsp-server` itself.

```bash
pip install python-lsp-pyre
```

or to make it a development requirement in Poetry

```bash
poetry add -G dev python-lsp-pyre
```

Then run `python-lsp-server` as usual, the plugin will be auto-discovered by `python-lsp-server` if you've installed it to the right environment. Refer to `python-lsp-server` and your IDE/text editor documentation on how to setup `python-lsp-server`. The plugin's default `enabled` status is `True`.

## Editor integration

* An example is provided for KDE's [Kate editor](/docs/kate.md)

## Configuration

Meta's Pyre uses `.pyre_configuration` files in your project to set up lint controls. It does not read `pyproject.toml`.

On first run of this plugin, it will detect a missing `.pyre_configuration` and write out one for you if the `create-pyre-config` [configuration](docs/Configuration.md) option is enabled. It relies on the workspace root passed to the language server for this write. This file is not immutable, and the [reference documentation](https://pyre-check.org/docs/configuration/) may be useful.

You can also use `pyre init` instead to set up the configuration.

The configuration written by this plugin is:

```json
{
    "site_package_search_strategy": "all",
    "source_directories": [
        "."
    ],
    "exclude": [
        "/setup.py",
        ".*/build/.*"
    ],
    "strict": true
}
```

The noteable difference from `pyre init` is the change to the search strategy ("pep561" to "all"), and turning on strict mode as the default. You may find strict mode a bit pedantic, but having worked with strict mode for several years, I highly recommend it.

If the `.pyre_configuration` file is not present (or has a syntax error), the LSP error log, LSP output, and your editor's LSP messages will display an ABEND message containing the error from Pyre as it fails to run.

## Squelching Pyre lint errors

The recommended way of squelching a Pyre warning is to pick one of `# pyre-ignore` or `# pyre-fixme`. More precisely, suppose Pyre is indicating

```
Missing global annotation [5]: Globally accessible variable `logger` has type `logging.Logger` but no type is specified.
```

at you, and you do not feel like typing your logger right now. On the line before, you can put either one of

* `# pyre-ignore[5] Don't care about logger`
* `# pyre-fixme[5] Resolve this when doing all logger work`

to squelch the lint, and provide a hint to future you (or other readers of the code). This is a trivial example; it's easier to just type the logger.

You do not need to match the number in the brackets, other than for ease of cross-reference with the [type errors documentation](https://pyre-check.org/docs/errors/).

When you address the squelched error, Pyre will indicate that the comment is not suppressing a type error and can be removed.

## Developing

Install development dependencies with (you might want to create a virtualenv first):

```bash
git clone https://github.com/cricalix/python-lsp-pyre python-lsp-pyre
cd python-lsp-pyre
pip install -e '.[dev]'
```

Alterately, if you use Poetry,

```bash
git clone https://github.com/cricalix/python-lsp-pyre python-lsp-pyre
cd python-lsp-pyre
poetry install
```

will set up a virtualenv if necessary, install all dependencies, and then install this project in editable/development mode.

## Contributing

This plugin was written to scratch an itch. If you find it useful, great!

If something about it annoys you, or you think there's a better way to do something, you're welcome to send a PR.
