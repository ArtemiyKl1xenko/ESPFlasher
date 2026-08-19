# ESPFlasher
Программа для прошивки плат ESP, ничем не отличающаяся от других таких программ.

Чем уникальна? - ничем

Для использования скачиваем файл из Releases и пишем в терминал
```
cd "Путь к корневой папке"
pip install -r requirements.txt
```
* **esptool** (>=5.3.1) — основная утилита для прошивки и взаимодействия с чипами ESP32/ESP8266.
* **pyserial** (>=3.5) — для работы с COM-портами компьютера.
* **requests** (>=2.31.0) — для отправки HTTP-запросов (проверка обновлений, скачивание прошивок).
* **pillow** (>=10.0.0) — для обработки изображений и иконок в графическом интерфе

Попрошу также не кидаться тапками из-за вайбкодинга.# ESPFlasher
Программа для прошивки плат ESP, ничем не отличающаяся от других таких программ.

**Чем уникальна?** — ничем.

### Как запустить из исходного кода
Скачиваем файлы проекта, открываем терминал в корневой папке и пишем:
```bash
# 1. Клонируем репозиторий
git clone https://github.com/ArtemiyKl1xenko/ESPFlasher/
cd ESPFlasher/cmexy9ltiHa

# 2. Устанавливаем зависимости
pip install -r requirements.txt

# 3. Запускаем
python launcher.py
```

### 🐧 Важно для Linux

1. **Зависимости интерфейса:** В Linux библиотека `tkinter` часто не идет в комплекте с Python. Если интерфейс не открывается, установите её через системный пакетный менеджер:
   * **Ubuntu/Debian:** `sudo apt install python3-tk`
   * **Arch Linux:** `sudo pacman -S tk`

2. **Права на COM-порт:** Чтобы программа могла шить ESP через USB, вашему пользователю нужны права на чтение/запись последовательного порта (обычно `/dev/ttyUSB0` или `/dev/ttyACM0`). Выдайте их командой:
   ```bash
   sudo usermod -aG dialout \$USER
   ```
   *(После этого нужно перезагрузить ПК или перезайти в систему).*

### Зависимости
* **esptool** (>=5.3.1) — основная утилита для прошивки и взаимодействия с чипами ESP32/ESP8266.
* **pyserial** (>=3.5) — для работы с COM-портами компьютера.
* **requests** (>=2.31.0) — для отправки HTTP-запросов (проверка обновлений, скачивание прошивок).
* **pillow** (>=10.0.0) — для обработки изображений и иконок в графическом интерфейсе.

### Как собрать в один кликабельный файл
Если захочется скомпилировать проект самостоятельно, установите `pyinstaller` (`pip install pyinstaller`), перейдите в папку с кодом программы и запустите:

**На Windows (.exe):**
```bash
pyinstaller --onefile --noconsole --distpath ".\dist" --add-data "core;core" --add-data "integrations;integrations" --add-data "ui;ui" --add-data "utils;utils" --paths ".." --hidden-import="esptool" --hidden-import="serial" --hidden-import="requests" --hidden-import="PIL" cmexy9ltiHa.py
```

**На Linux (бинарник):**
```bash
pyinstaller --onefile --noconsole --distpath "./dist" --add-data "core:core" --add-data "integrations:integrations" --add-data "ui:ui" --add-data "utils:utils" --paths ".." --hidden-import="esptool" --hidden-import="serial" --hidden-import="requests" --hidden-import="PIL" cmexy9ltiHa.py
```
*(Готовый файл появится в папке `dist` внутри проекта).*

---
Попрошу также не кидаться тапками из-за вайбкодинга.
