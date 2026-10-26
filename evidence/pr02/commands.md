## Разобранные команды
**1. `pwd`** — print working directory, печатает полный путь текущего каталога.
Результат: `/home/danil/robotics_ws`.

**2. `mkdir -p src evidence/pr02`** — создаёт каталоги, включая вложенные; ключ `-p`
не даёт ошибку, если каталог уже есть. Результат: каталоги `src/` и `evidence/pr02/`.

**3. `tee evidence/pr02/build.txt`** — читает stdin и одновременно пишет его в файл и в stdout.
Используется с `set -o pipefail`: конвейер `colcon build 2>&1 | tee build.txt`
сохраняет лог и оставляет ненулевой код возврата colcon, даже если сам `tee`
завершился успешно. Результат: `evidence/pr02/build-empty.txt` и `build.txt`.

**`>` против `|`**: `>` перенаправляет stdout программы в файл; `|` передаёт stdout первой программы на stdin
второй.

**`source` против запуска новой программы**: `source setup.bash` выполняет скрипт
в текущем терминале. Запуск новой программы (например, `ros2 launch`) выполняется
в отдельном процессе, его переменные после завершения исчезают.

## Создание пакета

```bash
cd src
ros2 pkg create --build-type ament_python --license Apache-2.0 \
  turtle_bringup --dependencies launch launch_ros turtlesim
cd ..
ls src/turtle_bringup
cat src/turtle_bringup/package.xml
```

## Сборка

Пустой пакет (до добавления launch):

```bash
set -o pipefail
colcon build --symlink-install --packages-select turtle_bringup \
  2>&1 | tee evidence/pr02/build-empty.txt
```

После добавления `launch/sim.launch.py` и `glob` в `setup.py`:

```bash
set -o pipefail
colcon build --symlink-install --packages-select turtle_bringup \
  2>&1 | tee evidence/pr02/build.txt
source install/setup.bash
ros2 pkg prefix turtle_bringup
# /home/danil/robotics_ws/install/turtle_bringup — путь из install workspace
ls "$(ros2 pkg prefix turtle_bringup)/share/turtle_bringup/launch"
# sim.launch.py — launch-файл установлен как ресурс пакета
```

## Запуск (терминал A)

```bash
source /opt/ros/lyrical/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=128
ros2 launch turtle_bringup sim.launch.py
```

Открылось одно окно turtlesim. Вывод в `nodes.txt`: нода `/turtlesim` видна
в графе (`ros2 node list --no-daemon --spin-time 2`).

## Команда и движение (B — публикация, C — поза)

Тип и поля сообщения — в `types.md`. Команды наблюдения в C:

```bash
ros2 interface show geometry_msgs/msg/Twist
ros2 topic type /turtle1/pose
ros2 topic echo /turtle1/pose --once
```

Поза до (`pose-before.txt`):

```
x: 5.544444561004639
y: 5.544444561004639
theta: 0.0
```

Публикация в B:

```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

Ожидалось: движение вперёд и поворот против часовой стрелки. Поза после
(`pose-after.txt`):

```
x: 6.509308815002441
y: 5.796990871429443
theta: 0.5040000081062317
```

Координаты и угол изменились — команда дошла; `linear_velocity` и
`angular_velocity` снова равны 0: одна публикация не задаёт бесконечное
движение, turtlesim остановился.

## Сбой: неверное полное имя топика

В B запущен непрерывный издатель в неверный топик:

```bash
ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

Пока он работает, сравнение конечных точек в C:

```bash
ros2 topic info /cmd_vel --verbose
ros2 topic info /turtle1/cmd_vel --verbose
```

Полный вывод в `info-broken.txt`:

| Топик | Publisher count | Subscription count |
|---|---|---|
| `/cmd_vel` | 1 (`_ros2cli_*`) | **0** |
| `/turtle1/cmd_vel` | 0 | 1 (`turtlesim`) |

Черепаха не двигается.

## Исправление: изменено только имя топика

```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

Поза после исправления (`pose-fixed.txt`): `x: 7.232…`, `theta: 1.008…` —
черепашка снова прошла дугу и остановилась после завершения публикации.

## Остановка

`Ctrl+C` в A завершает launch вместе с запущенным turtlesim; повторный
`ros2 node list --no-daemon --spin-time 2` не вернул ни одной ноды.

## Почему правильного типа недостаточно

DDS-соединение строится по полному имени топика и совместимому типу: подписчик
`turtlesim` слушает `/turtle1/cmd_vel`, и публикация в `/cmd_vel` — это другой
канал с тем же типом. Обнаружение (нода видна в `node list`, издатель виден
в `topic info`) не означает доставки: доставка происходит только между
издателем и подписчиком с совпавшими именами, что и показывают счётчики
конечных точек выше.
