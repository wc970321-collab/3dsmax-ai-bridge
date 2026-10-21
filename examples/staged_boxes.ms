-- Adds three sample boxes, one at a time. Does not reset or render the scene.
-- Dimensions use current scene system units. Run in an empty test scene.
undo "Bridge staged boxes" on
(
    for i = 1 to 3 do
    (
        box name:(uniqueName "Bridge_Demo_") width:40 length:40 height:(i*20) pos:[i*60,0,0]
        completeRedraw()
        windows.processPostedMessages()
        sleep 0.5
    )
)
