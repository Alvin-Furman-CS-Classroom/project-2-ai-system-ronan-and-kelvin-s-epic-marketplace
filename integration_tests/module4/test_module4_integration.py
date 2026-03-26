"""
Integration tests: Module 4 LTR on top of Modules 1–3.

Replace placeholders when pipeline and scoring are implemented.
"""


def test_module4_package_importable():
    import src.module4 as m4

    assert m4.__doc__
    assert "LearningToRankError" in m4.__all__
