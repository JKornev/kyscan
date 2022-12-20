# kyscan
Simple quake3 port scanner that is able to scan for:
- Quake3 server ports
- Qwfwd proxy ports

Based on [q3net](https://github.com/JKornev/q3net) project

![demo](https://dos-ninja-store.s3.amazonaws.com/data/django-summernote/2022-12-20/c26bc388-ccaa-439f-9f93-b73f63f8be05.gif)

## Usage
Fast scan verifies the most frequent ports
```
kyscan.py fast fpsclasico.de
```

Use full scan to scan full ports range 1-65536. But you have to worry about additional options to avoid slow scanning and blocking scanning attemprs
```
kyscan.py --pool 1024 --timeout 5.0 full fpsclasico.de
```

Moreover you can scan specific port range
```
kyscan.py range -p 1024 -t 5.0 27960 300010 -wp fpsclasico.de
```

Or just execute the script to get help
```
kyscan.py
```
