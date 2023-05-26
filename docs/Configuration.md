# Configuration

Like other Python Language Server plugins, configuration of the plugin is achieved by sending settings to the server from the client via `workplace/didChangeConfiguration`.

This plugin recognises the following configuration options.

| Key | Type | Default | Purpose |
| --- | --- | --- | --- |
| `pylsp.plugins.pyre.enabled` | `boolean` | True | Enable or disable this plugin. |
| `pylsp.plugins.pyre.create-pyre-config` | `boolean` | False | Whether to create a default .pyre_configuration file |

