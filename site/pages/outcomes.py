"""Results top: the tracking issues and the result pages, following the repository."""
from lib import bi
from pages.home import page_table, themes_table


def build():
    return f'''<div class="home">
<section><h2>Themes (tracking issues)</h2>{themes_table()}</section>
<section><h2>Pages</h2>{page_table('out')}</section>
</div>'''
