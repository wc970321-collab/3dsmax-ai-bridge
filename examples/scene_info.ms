-- Read-only: print current scene details in the MAXScript Listener.
format "Scene: %\nObjects: %\nRenderer: %\n" (maxFilePath + maxFileName) objects.count (classOf renderers.current)
