[app]
title = Зерновой Мастер
package.name = grainmaster
package.domain = org.example
source.dir = .
source.include_exts = py,kv,json
version = 1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1

[android]
api = 30
minapi = 21
android.accept_sdk_license = True
android.archs = arm64-v8a
android.ndk = 25b
p4a.branch = master
