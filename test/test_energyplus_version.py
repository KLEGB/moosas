from __future__ import annotations

from eppy.modeleditor import IDF
import pytest

from MoosasPy.model.io.idf.version import (
    ENERGYPLUS_VERSION,
    bundled_idd_path,
    bundled_template_idf_path,
    configure_idd,
    idd_version,
    idf_version,
    require_idf_version,
)


def test_bundled_energyplus_resources_are_26_1():
    assert ENERGYPLUS_VERSION == "26.1"
    assert idd_version(bundled_idd_path()) == "26.1"
    assert idf_version(bundled_template_idf_path()) == "26.1"

    configure_idd()
    template = IDF(str(bundled_template_idf_path()))
    assert str(template.idfobjects["VERSION"][0].Version_Identifier) == "26.1"


def test_old_idf_is_rejected_before_parsing(tmp_path):
    old_idf = tmp_path / "old.idf"
    old_idf.write_text("Version,24.2;\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"requires EnergyPlus 26\.1 IDF input.*got 24\.2"):
        require_idf_version(old_idf)
