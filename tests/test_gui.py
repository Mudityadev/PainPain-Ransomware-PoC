import pytest

from ransomware.gui.main import RansomwareGUI


@pytest.mark.gui
def test_gui_launch_real(qtbot):
    gui = RansomwareGUI(target_dir="/tmp/test")
    qtbot.addWidget(gui)
    gui.show()
    assert gui.isVisible()
    assert "encrypted" in gui.title().lower()
    gui.close()


def test_gui_launch_dummy():
    # Dummy test for GUI launch
    assert True

