# ПР01. Окружение и граф ROS 2

## Среда

- ОС: Ubuntu 26.04.1 LTS, архитектура x86_64, запуск native (без Docker/WSL).
- ROS: дистрибуция `lyrical` (`/opt/ros/lyrical`), RMW — `rmw_fastrtps_cpp` (см. `evidence/pr01/doctor.txt`).
- Гарантированный набор из трёх терминалов A, B, C в одной сессии.

Инициализация каждого терминала:

```bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=128
```

В терминале C подготовлен каталог отчёта:

```bash
mkdir -p evidence/pr01
ros2 doctor --report > evidence/pr01/doctor.txt 2>&1
```

## 1. Исправный граф (обе ноды в домене 128)

### Запуск

- Терминал A — симулятор: `ros2 run turtlesim turtlesim_node` (занимает терминал до Ctrl+C).
- Терминал B — управление: `ros2 run turtlesim turtle_teleop_key`. Нажатия стрелок двигают черепаху (проверено).
- Терминал C — наблюдение:

```bash
{
  echo "=== node list ==="
  ros2 node list --no-daemon --spin-time 2
  echo "=== topic list -t ==="
  ros2 topic list --no-daemon -t
  echo "=== node info /turtlesim ==="
  ros2 node info --no-daemon /turtlesim
  echo "=== topic type /turtle1/pose ==="
  POSE_TYPE=$(ros2 topic type --no-daemon /turtle1/pose)
  echo "POSE_TYPE=$POSE_TYPE"
  echo "=== topic echo --once ==="
  timeout 5s ros2 topic echo --no-daemon /turtle1/pose "$POSE_TYPE" --once
  printf 'exit=%s\n' "$?"
  echo "=== topic hz (10s) ==="
  time timeout 10s ros2 topic hz /turtle1/pose
} 2>&1 | tee evidence/pr01/observed.txt
```

### Вывод наблюдений (evidence/pr01/observed.txt)

Ноды:

```
/teleop_turtle
/turtlesim
```

Топики с типами (`ros2 topic list --no-daemon -t`):

```
/parameter_events [rcl_interfaces/msg/ParameterEvent]
/rosout [rcl_interfaces/msg/Log]
/turtle1/cmd_vel [geometry_msgs/msg/Twist]
/turtle1/color_sensor [turtlesim_msgs/msg/Color]
/turtle1/pose [turtlesim_msgs/msg/Pose]
```

Тип позы (`ros2 topic type --no-daemon /turtle1/pose`):

```
turtlesim_msgs/msg/Pose
```

Поза (`ros2 topic echo --no-daemon /turtle1/pose turtlesim_msgs/msg/Pose --once`):

```
x: 7.560444355010986
y: 5.544444561004639
theta: 0.0
linear_velocity: 0.0
angular_velocity: 0.0
---
exit=0
```

### Ноды и их роли

| Нода | Роль | Издаёт | Подписана на |
|---|---|---|---|
| `/turtlesim` | симулятор (движение, физика, поза) | `/turtle1/pose`, `/turtle1/color_sensor` | `/turtle1/cmd_vel` |
| `/teleop_turtle` | управление с клавиатуры | `/turtle1/cmd_vel` | — |

### Полные имена топиков и типы

| Топик | Тип | Назначение |
|---|---|---|
| `/turtle1/pose` | `turtlesim_msgs/msg/Pose` | положение черепахи (издатель `/turtlesim`) |
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | команды движения (издатель `/teleop_turtle`) |
| `/turtle1/color_sensor` | `turtlesim_msgs/msg/Color` | датчик цвета |
| `/parameter_events` | `rcl_interfaces/msg/ParameterEvent` | служебный (параметры) |
| `/rosout` | `rcl_interfaces/msg/Log` | журналирование |

### Замер частоты `ros2 topic hz /turtle1/pose`

Длительность замера — 10.6 c (реальный таймер `time timeout 10s`). Частота устойчиво держится ~62.5 Гц (окно 62 → 374 сообщений):

```
average rate: 62.514   min: 0.015s max: 0.017s  window: 62
average rate: 62.496   min: 0.014s max: 0.018s  window: 374
real 0m10,643s
```

Ориентир задания ~60–62.5 Гц (таймер turtlesim 16 мс) — замер укладывается. Сообщение `failed to initialize wait set...` в конце — артефакт прерывания команды `timeout`, на измерение не влияет.

## 2. Разрыв связи (подписчик переведён в домен 129)

- Терминал B: Ctrl+C у `turtle_teleop_key`, затем:

```bash
export ROS_DOMAIN_ID=129
ros2 run turtlesim turtle_teleop_key
```

- Терминал C — та же область, что у нового подписчика:

```bash
export ROS_DOMAIN_ID=129
ros2 node list --no-daemon --spin-time 2
timeout 5s ros2 topic echo --no-daemon /turtle1/pose "$POSE_TYPE" --once > evidence/pr01/pose-broken.txt 2>&1
printf 'exit=%s\n' "$?"
```

Наблюдение: `ros2 node list` видит только `/teleop_turtle` (нет `/turtlesim` — симулятор остался в домене 128). Поза не поступает: команда исчерпывает таймаут 5 секунд, `exit=124`, файл `pose-broken.txt` не содержит данных позы. Стрелки в терминале B перестали двигать черепаху.

## 3. Восстановление связи (возврат в исходный домен 128)

- Терминал B: Ctrl+C у teleop, затем:

```bash
export ROS_DOMAIN_ID=128
ros2 run turtlesim turtle_teleop_key
```

- Терминал C:

```bash
export ROS_DOMAIN_ID=128
ros2 node list --no-daemon --spin-time 2
timeout 5s ros2 topic echo --no-daemon /turtle1/pose "$POSE_TYPE" --once > evidence/pr01/pose-fixed.txt 2>&1
printf 'exit=%s\n' "$?"
```

Наблюдение: видны обе ноды — `/turtlesim` и `/teleop_turtle`. Поза приходит (evidence/pr01/pose-fixed.txt):

```
x: 7.560444355010986
y: 5.544444561004639
theta: 2.0160000324249268
linear_velocity: 0.0
angular_velocity: 0.0
```

`exit=0`. Стрелки снова двигают черепаху.

## Сравнение «до / сбой / после»

| Фаза | Домен издателя `/turtlesim` | Домен подписчика (CLI C) | Видимые ноды | Поза | exit |
|---|---|---|---|---|---|
| до (исправно) | 128 | 128 | `/turtlesim`, `/teleop_turtle` | приходит (`x=7.56, y=5.54`) | 0 |
| сбой | 128 | 129 | только `/teleop_turtle` | не приходит | 124 |
| после | 128 | 128 | `/turtlesim`, `/teleop_turtle` | приходит (`theta=2.016`) | 0 |

## Объяснение

`ROS_DOMAIN_ID` задаёт область обнаружения участников DDS (discovery). Значение применяется **при запуске процесса** ноды: `export` не перенастраивает уже работающую ноду. Поэтому:

- чтобы увести подписчика в домен 129, `turtle_teleop_key` пришлось **перезапустить** уже с новым доменом — так родился подписчик вне области видимости симулятора;
- симулятор `/turtlesim` перезапускать не потребовалось: он всё время работал в домене 128, а «сломанный» подписчик в 129 просто не обнаруживал его издателя;
- установку ROS менять не требовалось: изоляция — это штатное свойство discovery по доменам, а не сбой окружения.

После возврата подписчика в домен 128 discovery снова сводит издателя и подписчика, и поза приходит — связь восстановлена тем же наблюдением, что и в начале.
