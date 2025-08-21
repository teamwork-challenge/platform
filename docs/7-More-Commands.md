# Client Command Extensions

## Logging Configuration

A new command is needed to configure the logging level

`cli config log-level <destination> <level>`

* destination is either `file` or `console`
* level is one of `NONE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`
* default levels:
  * console — NONE
  * file — INFO
* The logging levels should be persisted in the config file.

## Competition Endpoint Configuration

A command is needed to set or update the competition server address.
`cli config api-url <url>`

* url may contain port if it is not default 80.
* These values should be stored in the config file and persist across runs.

## Help Behavior

* If a user enters an invalid or malformed command, help output should be shown immediately.
  * The user should not have to manually specify `--help` in such cases.

## Teams

`cli team list <challenge-id>`
* A admin command to list all registered commands.
* This command must output the list with all team fields, including:
  * Command ID
  * Associated API key
