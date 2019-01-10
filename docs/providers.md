# Providers

giTracks has notion of providers which are the backends where the time entries are stored. This page has overview of them
and their's capabilities.

## Toggl

Provider for time-tracking service [toggl.com](https://toggl.com)

> Task support: **Yes**
>
> Project support: **Yes**

Additional capabilities:

* Possible to define a tags for all the giTrack's entries.
 
### INI options
 
| Name | Type | Default | Description |
| -----|----- |-------- | ----------- |
| api_token | `str` | | API token that defines the account to which the entries will be saved to. |
| tags | `list` | | List of tags that will be added to the time entry. For example `['gitrack', 'some other tag']` |
 