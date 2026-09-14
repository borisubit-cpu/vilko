[app]
title = GrainMaster
package.name = grainmaster
package.domain = orgexample
source.dir = .
source.include_exts = py,kv,json
version = 1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 0

[android]
api = 30
minapi = 21
android.accept_sdk_license = True
android.archs = arm64-v8a
android.ndk = 25b
p4a.branch = develop
