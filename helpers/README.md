#Helper Files for Emmamusic

## Shutdown Service Unit file
Put File emmamusic-poweroff.service in /etc/systemd/system/emmamusic-poweroff.service and run 
```
cd /etc/systemd/system/
sudo systemctl enable emmamusic-poweroff.service
```

## Supervisor Program Config Files
After installing supervisord put files
* emmamusic.conf
* powerdown.conf
in directory `/etc/supervisor/conf.d`
