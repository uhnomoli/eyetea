import logging

import rich.text
import textual.containers
import textual.message
import textual.widgets

# TODO: check for less ugly way to do this import
from textual.widgets._collapsible import CollapsibleTitle

from .. import events


class EventEntryTitle(CollapsibleTitle):
    COMPONENT_CLASSES = {
        'event-entry-title--error',
        'event-entry-title--error-muted',
        'event-entry-title--highlight',
        'event-entry-title--highlight-muted',
        'event-entry-title--info',
        'event-entry-title--info-muted',
        'event-entry-title--success',
        'event-entry-title--success-muted'}
    ICON_MAP = {
        events.Source.HTTP_REQUEST: '\u2192',
        events.Source.HTTP_RESPONSE: '\u2190'}
    MESSAGE_MAP = {
        events.Source.HTTP_REQUEST: lambda entry: \
            entry.data['request']['method'],
        events.Source.HTTP_RESPONSE: lambda entry: \
            entry.data['response']['status']}


    def __init__(self, *args, entry, **kwargs):
        super().__init__(*args, label='', **kwargs)

        self.entry = {
            'icon': '',
            'level': entry.level,
            'message': entry.message.split('_', 1)[1],
            'path': entry.data['request']['url']['path'],
            'time': entry.asctime.replace(',', '.')}

        if entry.source in self.ICON_MAP:
            self.entry['icon'] = f' {self.ICON_MAP[entry.source]} '

        if entry.source in self.MESSAGE_MAP:
            self.entry['message'] = self.MESSAGE_MAP[entry.source](entry)


    def render(self):
        indicator = self.expanded_symbol
        if self.collapsed:
            indicator = self.collapsed_symbol

        self.label = rich.text.Text.assemble(
            (f'{indicator} ',),
            (
                self.entry['icon'],
                self.get_component_rich_style(
                    'event-entry-title--highlight-muted')),
            (
                f' {self.entry["time"]} ',
                self.get_component_rich_style(
                    f'event-entry-title--{self.entry["level"]}-muted')),
            (
                f' {self.entry["message"]} ',
                self.get_component_rich_style(
                    f'event-entry-title--{self.entry["level"]}')),
            (
                f' {self.entry["path"]} ',
                self.get_component_rich_style(
                    'event-entry-title--highlight')))

        return self.label

class EventEntry(textual.widgets.Collapsible):
    DATA_MAP = {
        events.Source.HTTP_REQUEST: lambda entry: entry.data['request'],
        events.Source.HTTP_RESPONSE: lambda entry: entry.data['response']}


    def __init__(
            self,
            *,
            collapsed=True,
            collapsed_symbol='+',
            entry,
            expanded_symbol='-',
            **kwargs):
        super(textual.widgets.Collapsible, self).__init__(**kwargs)

        for attribute in ('data', 'level', 'source'):
            if not hasattr(entry, attribute):
                raise ValueError(f'entry is missing {attribute}')

        data = entry.data
        if entry.source in self.DATA_MAP:
            data = self.DATA_MAP[entry.source](entry)

        log = textual.widgets.RichLog()
        log.write(data)

        self._title = EventEntryTitle(
            collapsed=collapsed,
            collapsed_symbol=collapsed_symbol,
            entry=entry,
            expanded_symbol=expanded_symbol)

        # reimplement `textual.widgets.Collapsible.__init__()` behavior so we
        # use our own title widget
        self._contents_list = [log]
        self.collapsed = collapsed
        self.title = self._title.label

