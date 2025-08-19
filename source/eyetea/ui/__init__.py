import json
import multiprocessing

import textual
import textual.app
import textual.binding
import textual.containers
import textual.content
import textual.css.query
import textual.highlight
import textual.widgets

from .. import events


class UI(textual.app.App):
    BINDINGS = [
        textual.binding.Binding('ctrl+c', 'copy'),
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
        self.query_one('#events-eyetea').border_title = '\\[ events :: eyetea ]'
        self.query_one('#events-http').border_title = '\\[ events :: http ]'
        self.query_one('#downloads').border_title = '\\[ downloads ]'

    def on_unmount(self):
        self.server_log_stop()
        self.server_stop()


    def server_log_entry_create(self, entry):
        for attribute in ('data', 'level', 'source'):
            if not hasattr(entry, attribute):
                raise ValueError(f'server log entry is missing {attribute}')

        data = events.DATA_MAP.get(entry.source, None)
        data = data(entry) if data else entry.data

        foreground = entry.level == events.Level.INFO
        foreground = 'primary' if foreground else f'{entry.level}'

        message = events.MESSAGE_MAP.get(entry.source, None)
        message = message(entry) if message else entry.message.split('_', 1)[1]

        icon = events.ICON_MAP.get(entry.source, '')
        path = entry.data['request']['url']['path']
        time = entry.asctime.replace(',', '.')

        content = json.dumps(data, indent=4, sort_keys=True)
        content = textual.highlight.highlight(
            content, language='json', tab_size=4)

        title = textual.content.Content().join([
            textual.content.Content.from_markup(
                '[$foreground-muted on $surface] $icon [/]', icon=icon),
            textual.content.Content.from_markup(
                f'[$text-{foreground} on ${foreground}-muted] $time [/]',
                time=time),
            textual.content.Content.from_markup(
                f'[$foreground on ${foreground}-darken-2] $message [/]',
                message=message),
            textual.content.Content.from_markup(
                '[$foreground on $surface-lighten-2] $path [/]', path=path)])

        return textual.widgets.Collapsible(
            textual.widgets.Static(content),
            collapsed_symbol='+',
            expanded_symbol='-',
            title=title)

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

        widget = self.server_log_entry_create(entry)

        await container.mount(widget, before=0)


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

