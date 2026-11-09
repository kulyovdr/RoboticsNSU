# Robotics workspace — PR03

Практическая работа PR03: первая собственная нода `patrol` — подписка на позу
turtlesim, таймер и публикация команд Twist; разрыв имени топика и remap.
Окружение: Ubuntu 26.04, ROS 2 Lyrical, RMW `rmw_fastrtps_cpp`.

## Требования

- ROS 2 Lyrical с `rclpy`, `geometry_msgs`, `turtlesim_msgs`, `turtlesim`, `colcon`;
- пакет `turtle_bringup` из PR02 для запуска симулятора;
- терминалы: T (сборка), A (симулятор), B (нода), C (наблюдение).

## Сборка

```bash
source /opt/ros/lyrical/setup.bash
colcon build --symlink-install --packages-select patrol
source install/setup.bash
ros2 pkg prefix patrol
```

## Запуск

В каждом терминале: `source /opt/ros/lyrical/setup.bash; source install/setup.bash;
export ROS_DOMAIN_ID=128`.

```bash
# A — симулятор
ros2 launch turtle_bringup sim.launch.py
# B — нода с remap: издатель cmd_vel соединяется с /turtle1/cmd_vel
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
# C — наблюдение
ros2 node list --no-daemon --spin-time 2
timeout 10 ros2 topic hz /turtle1/cmd_vel
```

Без remap издатель попадает в относительный `/cmd_vel` без подписчиков —
черепашка стоит; это демонстрирует отличие обнаружения от доставки.

## Поведение ноды

Подписка на `/turtle1/pose` сохраняет последнюю позу (callback только сохраняет);
таймер 0.1 с публикует Twist: до первой позы — нулевой, после — `linear.x=0.5`,
`angular.z=0.3`. Выбор команды — чистая функция `choose_cmd`, покрытая pytest.

## Evidence и CI

`evidence/pr03/`: `demo.md`, `tests.txt`, `report.json`.
CI job `pr03-build`: сборка patrol, pytest и `check_practice.py PR03` (kit w10).
Локально:

```bash
python3 -m pytest src/patrol/test
python3 .course-kit/v1/tools/check_practice.py PR03 --submission .
```
