-- Run once from Scripting > Run Script in 3ds Max 2020.
-- Only reads scene information on startup. No startup installation or network port.
global GPTMaxBridge
global GPTMaxBridgeRoot
global GPTMaxBridgeBusy = false
try (destroyDialog GPTMaxBridge) catch ()
GPTMaxBridgeRoot = getFilenamePath (getSourceFileName())

fn GPTMaxBridgeStatus message =
(
    local f = createFile (GPTMaxBridgeRoot + "bridge_status.txt")
    format "%\n%\n" (localTime as string) message to:f
    close f
)

rollout GPTMaxBridge "GPT Max Bridge" width:330 height:110
(
    label info "Local bridge running. Close this window to stop." pos:[10,12]
    label details "Waiting for commands..." pos:[10,38] width:310
    timer poll interval:1000 active:true
    on GPTMaxBridge open do
    (
        local f = createFile (GPTMaxBridgeRoot + "bridge_scene_info.txt")
        format "Max version: %\nScene: %\nObject count: %\nRenderer: %\nSystem unit: % %\n" (maxVersion()) (maxFilePath + maxFileName) objects.count (classOf renderers.current) units.SystemScale units.SystemType to:f
        try
        (
            local m = execute "VRayMtl()"
            format "V-Ray material class: %\nMaterial properties: %\n" (classOf m) (getPropNames m) to:f
        )
        catch (format "V-Ray probe error: %\n" (getCurrentException()) to:f)
        close f
        GPTMaxBridgeStatus "READY"
    )
    on poll tick do
    (
        local request = GPTMaxBridgeRoot + "bridge_request.ms"
        if (not GPTMaxBridgeBusy) and (doesFileExist request) do
        (
            GPTMaxBridgeBusy = true
            local archived = GPTMaxBridgeRoot + "bridge_request_" + ((timeStamp()) as string) + ".ms"
            try
            (
                (dotNetClass "System.IO.File").Move request archived
                details.text = "Executing command..."
                GPTMaxBridgeStatus "RUNNING"
                fileIn archived quiet:true
                GPTMaxBridgeStatus "OK"
                details.text = "Command finished."
            )
            catch
            (
                GPTMaxBridgeStatus ("ERROR: " + (getCurrentException()))
                details.text = "Command failed. See bridge_status.txt."
            )
            GPTMaxBridgeBusy = false
        )
    )
    on GPTMaxBridge close do GPTMaxBridgeStatus "STOPPED"
)
createDialog GPTMaxBridge
