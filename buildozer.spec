[app]
title = Vilko
package.name = vilko
package.domain = org.vilko
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

# Явно указываем совместимые версии Python (hostpython3 и python3 должны совпадать)
requirements = python3==3.13.9,hostpython3==3.13.9,kivy==2.3.1,openssl,sqlite3,pyjnius,android,setuptools,certifi,chardet,idna,requests,urllib3

orientation = portrait
fullscreen = 0
android.permissions = INTERNET

# Рекомендуемая версия NDK для стабильной сборки
android.ndk = 25c
android.api = 31
android.minapi = 21
android.archs = arm64-v8a

# Остальные настройки по умолчанию
