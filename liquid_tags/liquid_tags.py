from pelican import signals
from .mdx_liquid_tags import LiquidTags


def addLiquidTags(gen):
    if not gen.settings.get('MD_EXTENSIONS'):
        from pelican.settings import DEFAULT_CONFIG
        gen.settings['MD_EXTENSIONS'] = DEFAULT_CONFIG['MD_EXTENSIONS']

    if LiquidTags not in gen.settings['MD_EXTENSIONS']:
        ext = LiquidTags()
        ext.config['settings'] = gen.settings
        gen.settings['MD_EXTENSIONS'].append(ext)


def register():
    signals.initialized.connect(addLiquidTags)
