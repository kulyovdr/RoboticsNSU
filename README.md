# Robotics workspace — PR01

Практическая работа PR01: окружение ROS 2, граф нод turtlesim, разрыв и восстановление
связи между доменами. Запуск native на Ubuntu 26.04 LTS, ROS 2 Lyrical
(`/opt/ros/lyrical`), RMW `rmw_fastrtps_cpp`.

## Требования

- Ubuntu 26.04 (или WSL/контейнер) с установленным ROS 2 Lyrical;
- пакеты `turtlesim`, `turtlesim_msgs`;
- три Bash-терминала в одной сессии (A, B, C).

## Порядок запуска

Каждый терминал инициализируется одинаково:

```bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=128
```

### Терминал A — симулятор

```bash
ros2 run turtlesim turtlesim_node
```

### Терминал B — управление с клавиатуры

```bash
ros2 run turtlesim turtle_teleop_key
```

Стрелки двигают черепаху, пока фокус в терминале B.

### Терминал C — наблюдение за графом

```bash
ros2 node list --no-daemon --spin-time 2
ros2 topic list --no-daemon -t
ros2 node info --no-daemon /turtlesim
ros2 topic type --no-daemon /turtle1/pose
timeout 5s ros2 topic echo --no-daemon /turtle1/pose turtlesim_msgs/msg/Pose --once
time timeout 10s ros2 topic hz /turtle1/pose
```

Ожидание: обе ноды (`/turtlesim`, `/teleop_turtle`), тип позы `turtlesim_msgs/msg/Pose`,
частота публикации ~62.5 Гц.

## Опыт: разрыв и восстановление связи

1. **Разрыв.** В B остановите teleop (Ctrl+C), переключите B и C в другой домен и
   запустите подписчика заново:

   ```bash
   export ROS_DOMAIN_ID=129
   ros2 run turtlesim turtle_teleop_key        # в B
   ros2 node list --no-daemon --spin-time 2     # в C: только /teleop_turtle
   timeout 5s ros2 topic echo --no-daemon /turtle1/pose turtlesim_msgs/msg/Pose --once
   ```

   Поза не приходит, команда завершается по таймауту (exit=124). Симулятор остаётся
   в домене 128 и перезапуска не требует: `ROS_DOMAIN_ID` применяется при запуске
   процесса, `export` не перенастраивает работающую ноду.

2. **Восстановление.** Верните B и C в исходный домен и повторите проверку:

   ```bash
   export ROS_DOMAIN_ID=128
   ros2 run turtlesim turtle_teleop_key
   timeout 5s ros2 topic echo --no-daemon /turtle1/pose turtlesim_msgs/msg/Pose --once
   ```

   Поза приходит (exit=0), стрелки снова двигают черепаху.

## Evidence

Собирается в `evidence/pr01/`:

- `doctor.txt` — `ros2 doctor --report`;
- `graph.md` — команды, граф, типы, замер частоты, сравнение «до / сбой / после»;
- `environment.json` — способ запуска, версии ОС/ROS/Gazebo, RMW, домены опыта;
- `pose-broken.txt` / `pose-fixed.txt` — наблюдения фаз разрыва и восстановления;
- `report.json` — отчёт (в поле `commit` — SHA коммита реализации).

## CI

Workflow `.github/workflows/ci.yml` при каждом push проверяет JSON-файлы отчёта,
совпадение SHA-256 course kit и комплектность evidence через
`.course-kit/v1/tools/check_practice.py PR01 --submission .`.

Локальная проверка перед сдачей:

```bash
python3 .course-kit/v1/tools/check_practice.py PR01 --submission .
```
