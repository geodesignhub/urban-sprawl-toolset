# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    from .urban_sprawl_plugin import UrbanSprawlPlugin
    return UrbanSprawlPlugin()
