from dynamicalsystem.pytests.environment import variables as environment_variables
from os.path import join, exists
from os import environ

def test_watermark_file_exists(environment_variables):
    from dynamicalsystem.gazette.watermarks import Watermark
    
    _ = Watermark("signal_to_abyss")
    _.logger.info(f"Environment is '{environ.get("DYNAMICALSYSTEM_ENVIRONMENT", "unknown")}'")
    
    assert exists(_.watermark_file), f"Watermark file '{_.watermark_file}' does not exist"

def test_get_watermarks(environment_variables):
    from dynamicalsystem.gazette.watermarks import watermarks

    _ = watermarks()
    assert "signal_to_abyss" in _
    assert "bluesky" in _

