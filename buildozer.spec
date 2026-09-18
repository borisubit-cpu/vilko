[app]
title = Зерновой Мастер
package.name = grainmaster
package.domain = com.grainmaster
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,json
version = 1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/bg.png

[buildozer]
log_level = 2
warn_on_root = 0

[android]
api = 31
minapi = 21
android.accept_sdk_license = True
android.archs = arm64-v8a
android.ndk = 25b
p4a.branch = develop
