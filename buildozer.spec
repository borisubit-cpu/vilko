[app]
title = Зерновой Мастер
package.name = grainmaster
package.domain = com.grainmaster
source.dir = .
source.include_exts = py,png,jpg,jpeg
version = 1.0.1
requirements = python3,kivy
orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/icon.png
android.archs = arm64-v8a
android.accept_sdk_license = True
android.ndk = 25b
aandroid.api = 34
android.minapi = 21
android.release_artifact = apk
android.debug_artifact = apk

[buildozer]
log_level = 2
warn_on_root = 0
