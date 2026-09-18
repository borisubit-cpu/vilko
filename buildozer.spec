[app]
title = Зерновой Мастер
package.name = grainmaster
package.domain = com.grainmaster
source.dir = .
source.include_exts = py,png,jpg,jpeg
version = 1.0
requirements = python3,kivy==2.3.0
orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/icon.png
android.archs = arm64-v8a
android.accept_sdk_license = True
android.ndk = 25b
android.api = 31
android.minapi = 21

[buildozer]
log_level = 2
warn_on_root = 0
