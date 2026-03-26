"""Tests for the LTR pipeline end-to-end (module4.pipeline)."""


def test_pipeline_module_importable():
    import src.module4.pipeline as pipeline

    assert pipeline.__doc__ is not None
