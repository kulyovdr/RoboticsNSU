# Robotics workspace — PR02

Практическая работа PR02: пакет `turtle_bringup`, его сборка colcon, первый launch-файл
для готовой ноды turtlesim и проверка доставки команды через CLI. Окружение: Ubuntu 26.04, ROS 2 Lyrical, RMW `rmw_fastrtps_cpp`.

## Требования

- ROS 2 Lyrical с пакетами `turtlesim`, `launch`, `launch_ros`, утилита `colcon`;
- корень личного репозитория используется как корень workspace (`src/`, `build/`,
  `install/`, `log/`);
- терминалы: T (сборка) и A, B, C (запуск и наблюдения).

## Сборка пакета

Из корня workspace (терминал T):

```bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=128
set -o pipefail
colcon build --symlink-install --packages-select turtle_bringup \
  2>&1 | tee evidence/pr02/build.txt
source install/setup.bash
ros2 pkg prefix turtle_bringup
```

`set -o pipefail` сохраняет ненулевой код возврата colcon, даже если `tee` отработал
успешно. Пакет содержит `launch/sim.launch.py`, который устанавливается в
`share/turtle_bringup/launch` через `data_files` в `setup.py`.

## Порядок запуска

Каждый терминал (A, B, C) инициализируется одинаково:

```bash
source /opt/ros/lyrical/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=128
```

Старые экземпляры turtlesim и teleop перед запуском останавливаются.

### Терминал A — запуск симулятора через launch

```bash
ros2 launch turtle_bringup sim.launch.py
```

Открывается одно окно turtlesim. `Ctrl+C` завершает и launch, и запущенный им turtlesim.

### Терминал B — команды и граф

```bash
ros2 node list --no-daemon --spin-time 2
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

Одна публикация даёт короткий поворот и движение: без новых команд черепаха
останавливается.

### Терминал C — наблюдение

```bash
ros2 interface show geometry_msgs/msg/Twist
ros2 topic type /turtle1/pose
ros2 topic echo /turtle1/pose --once
```

Позу фиксируют до и после публикации Twist.

## Опыт: ошибка в полном имени топика

1. **Сбой.** Издаватель с неверным именем (в B):

   ```bash
   ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
     /cmd_vel geometry_msgs/msg/Twist \
     '{linear: {x: 1.0}, angular: {z: 0.5}}'
   ```

   Пока он работает, в C:

   ```bash
   ros2 topic info /cmd_vel --verbose
   ros2 topic info /turtle1/cmd_vel --verbose
   ```

   У `/cmd_vel` виден только издатель — подписчика turtlesim у него нет, черепаха
   не двигается: правильного типа сообщения недостаточно, важна доставляемость
   по полному имени.

2. **Исправление.** Остановить издателя, заменить только `/cmd_vel` на
   `/turtle1/cmd_vel`, повторить публикацию — движение возвращается.

## Evidence

Собирается в `evidence/pr02/`:

- `build-empty.txt` / `build.txt` — сборки пакета до и после добавления launch;
- `commands.md` — разобранные команды Linux, запуск/остановка launch, сравнение
  «до / сбой / после»;
- `types.md` — топики `/turtle1/cmd_vel`, `/turtle1/pose`, их типы и поля Twist;
- `report.json` — отчёт (в поле `commit` — SHA коммита реализации).

## CI

Workflow `.github/workflows/pr02.yml` при каждом push собирает `turtle_bringup`,
проверяет наличие установленного `sim.launch.py` и комплектность evidence через
`.course-kit/v1/tools/check_practice.py PR02 --submission .`.

Локальная проверка перед сдачей:

```bash
python3 -m py_compile src/turtle_bringup/launch/sim.launch.py
python3 .course-kit/v1/tools/check_practice.py PR02 --submission .
```
