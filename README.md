# Home Assistant UPB Integration

## Example configuration.yaml
```
upb:
 url: serial:///dev/cu.KeySerial1:4800
 file_path: ./upb.upe
```

The `url` is like a "real" url. `serial://` means connect using serial port. Anything that follows is the name of the device where the PIM is connected. So it could be something such as `COM1` on Windows or something such as `/dev/tty02` on Linux/Unix, or on a Mac the one you see above.

The `file_path` is the path and filename of the UPStart file export. The export file is in UPE format. The file should be placed in the hass `config` directory.

## Home Assistant Model

UPB devices (lights, switches, etc) are represented as Lights in Home Assistant. Turning the devices on and off as is supported.
Dimming is supported for devices that support dimming. Transition time is supported for devices that support dimming.

UPB Links are support as Lights in Home Assistant. Links support Activate, Deactivate, and Goto level.

## Development Status

This component is under active development. Treat this as an alpha level component.
That means that naming of devices, entity_ids, and unique_ids may change, meaning that your UPB configuration may need to be redone.

Feature suggestions, bug reports, and design thoughts all welcome.

## Debugging Information

Debug logs are useful when reporting a problem. Add the following to your `configuration.yaml` to turn on the UPB debug logs.

```
logger:
  default: info
  logs:
    custom_components.upb: debug
    upb_lib: debug
```
