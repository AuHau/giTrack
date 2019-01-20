# Contributing

Any contributions are welcomed.

Before doing any big contributions it is good idea to first discuss it in relevant issue to get good idea what sort of 
direction is the best and what sort of result will be accepted best.

Also it is welcomed if your PRs will contain test coverage.

## Tips for developing 

If you use environmental variable `GITRACK_STORAGE`, then you can specify through it where the giTrack's internal data 
storage will be directed for the running `gitrack` command. This is helpful especially when you need to test 
initializations and if you don't want to clutter your own giTrack storage.
 
## Custom provider

If you want to implement your own provider, create a class which inherits from `gitrack.providers.AbstractProvider`
and implement all the abstract methods. Then register it in `gitrack.Providers` enum.