# Configuration

giTrack has hierarchical configuration with three levels: 

1. Local config 
2. Store (eq. giTrack's internal storage)
3. Global config (eq. config file common for all Git repos)

The resolution of options is in order presented above. 
The config files (local and global) are INI styled text files that you can customize to your need.

## Local configuration

> `.gitrack` file placed in root of the Git repo

Local configuration is the first place where giTrack looks to for option resolution. It can be part of the Git repo
as common configuration for the team working in the repo.

## Store

> binary internal storage

Pickled giTrack's state with some level of configuration and some other data about repos.

## Global configuration

> `default.config` file placed in the OS-specific application configuration folder (see: `user_config_dir` in [appdirs](https://github.com/ActiveState/appdirs))

## INI options

Overview of options for the INI config files. All following options belongs under `[gitrack]` section.
This table display only the common giTrack's configuration. Each provider
can have different set of custom options. For that see the [provider's overview](./providers.md) you want to use.

| Name | Type | Default | Description |
| -----|----- |-------- | ----------- |
| provider | `str` | | Name of provider to be used. (**Required**) |
| project_support | `bool` | False | Defines if project's support is enabled. Provider needs to support it. |
| project | `str` | | Defines ID or Name of Project to be associated with the created time entries. |
| tasks_support | `bool` | False | Defines if task's support is enabled. Provider needs to support it. |
| tasks_mode | `str (enum)` | |  Possible values: `static`, `dynamic_branch` and `dynamic_message`. For explanation see [Task support](./usage.md#task-support). |
| tasks_regex | `str` | | Python Regex that defines how the task's name or ID. It needs to contain capturing group with name `task`. |
| tasks_value | `str` | | In case of `static` mode, the name or ID to be used. |
| update_check | `bool` | True | giTrack will check upon invocation if there is a newer version available. |
