from patrol.patrol import choose_cmd


class FakePose:
    pass


def test_no_pose_yields_zero_cmd():
    cmd = choose_cmd(None)
    assert cmd.linear.x == 0.0
    assert cmd.linear.y == 0.0
    assert cmd.angular.z == 0.0


def test_pose_yields_patrol_cmd():
    cmd = choose_cmd(FakePose())
    assert cmd.linear.x == 0.5
    assert cmd.angular.z == 0.3
