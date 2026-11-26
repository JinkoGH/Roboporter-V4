This code:
- Read the controller using XInput.
- Normalises joystick readings to approximately −1 to +1.  
- Converts button states into binary values.
- Sends controller data as JSON over HTTP.
- Updates approximately every 100 milliseconds.

# Windows Controller using XInput 

```shell
Add-Type @'
using System;
using System.Runtime.InteropServices;

public class GamepadTest {
    [DllImport("xinput1_4.dll")]
    public static extern uint XInputGetState(
        uint userIndex, out XINPUT_STATE state);

    [StructLayout(LayoutKind.Sequential)]
    public struct XINPUT_STATE {
        public uint packetNumber;
        public GAMEPAD gamepad;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct GAMEPAD {
        public ushort buttons;
        public byte leftTrigger;
        public byte rightTrigger;
        public short thumbLX;
        public short thumbLY;
        public short thumbRX;
        public short thumbRY;
    }
}
'@

$state = New-Object GamepadTest+XINPUT_STATE

[GamepadTest]::XInputGetState(0, [ref]$state)
$state.gamepad
```



# Live controller data transmission

```shell
while ($true) {
    $result = [GamepadTest]::XInputGetState(0, [ref]$state)

    if ($result -ne 0) {
        Write-Host "Controller disconnected"
        break
    }

    $g = $state.gamepad

    $axes = @(
        [double]$g.thumbLX / 32768
        [double]$g.thumbLY / 32768
        [double]$g.thumbRX / 32768
        [double]$g.thumbRY / 32768
        [double]$g.leftTrigger / 255
        [double]$g.rightTrigger / 255
    )

    $buttons = @(0..15 | ForEach-Object {
        if (($g.buttons -band (1 -shl $_)) -ne 0) {
            1
        } else {
            0
        }
    })

    $body = @{
        axes = $axes
        buttons = $buttons
    } | ConvertTo-Json -Compress

    try {
        Invoke-WebRequest `
            -Uri "http://localhost:8765/joy" `
            -Method POST `
            -ContentType "application/json" `
            -Body $body `
            -UseBasicParsing | Out-Null
    }
    catch {
        Write-Host "Cannot reach ROS 2 bridge"
        break
    }

    Start-Sleep -Milliseconds 100
}
```
