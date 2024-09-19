import multiprocessing

import textual
import textual.app
import textual.binding
import textual.color
import textual.containers
import textual.css.query
import textual.widgets

from . import widgets
from .. import events


class UI(textual.app.App):
    BINDINGS = [
        textual.binding.Binding('ctrl+z', 'suspend_process')]
    CSS_PATH = 'static/eyetea.tcss'


    def __init__(self, options, server):
        self.options = options
        self.instance = None
        self.server = server

        super().__init__()


    def compose(self):
        yield textual.containers.VerticalScroll(
            classes='box', id='events-eyetea', name='events-eyetea')
        if self.options.downloads:
            yield textual.widgets.DirectoryTree(
                classes='box',
                id='downloads',
                name='downloads',
                path=self.options.downloads)
        else:
            yield textual.widgets.Static(
                classes='box disabled', id='downloads', name='downloads')
        yield textual.containers.VerticalScroll(
            classes='box', id='events-http', name='events-http')

    def on_load(self):
        self.server_start()
        self.server_log_start()

    def on_mount(self):
        self.query_one('#events-eyetea').border_title = '[ events :: eyetea ]'
        self.query_one('#events-http').border_title = '[ events :: http ]'
        self.query_one('#downloads').border_title = '[ downloads ]'

    def on_unmount(self):
        self.server_log_stop()
        self.server_stop()


    @textual.work(exclusive=True, group='server_log', thread=True)
    def server_log_start(self):
        worker = textual.worker.get_current_worker()

        while True:
            if worker.is_cancelled:
                break

            entry = self.options.queue.get()
            if entry is None:
                break

            self.call_from_thread(self.server_log_write, entry)

    def server_log_stop(self):
        self.options.queue.put_nowait(None)

    async def server_log_write(self, entry):
        source = getattr(entry, 'source', None)
        if not isinstance(source, events.Source):
            return

        source_root = source.value.split('_', 1)[0]
        try:
            container = self.query_one(f'#events-{source_root}')
        except textual.css.query.NoMatches:
            return

        widget = widgets.EventEntry(entry=entry)

        await container.mount(widget, before=0)

        for widget in container.query('EventEntry')[:2]:
            widget.toggle_class('first')


    @textual.work(exclusive=True, group='server', thread=True)
    def server_start(self):
        if self.instance is None:
            self.instance = multiprocessing.Process(
                kwargs={
                    'host': self.options.host,
                    'port': self.options.port,
                    'use_reloader': False},
                target=self.server.run)
            self.instance.start()

            # TODO: handle server error if we've reached here
            self.instance.join()
            self.exit(1)

    def server_stop(self):
        if self.instance is not None and self.instance.is_alive():
            self.instance.terminate()

