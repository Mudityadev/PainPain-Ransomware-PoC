import pytest
from ransomware.gui.main import RansomwareGUI

@pytest.mark.gui
def test_gui_launch(qtbot):
    gui = RansomwareGUI(target_dir="/tmp/test")
    qtbot.addWidget(gui)
    gui.show()
    assert gui.isVisible()
    assert "encrypted" in gui.title().lower()
    gui.close() 