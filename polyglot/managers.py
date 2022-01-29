import os
import json
from abc import ABC, abstractmethod

import polib
import colorama
import progressbar

from polyglot import deepl_request


class Manager(ABC):

    def __init__(self, deepl: deepl_request.DeeplRequest, source_file: str, output_directory: str = '') -> None:
        self.source_file = source_file
        self.check_source_file()
        self.deepl = deepl
        self.output_directory = output_directory if output_directory != '' and os.path.isdir(
            output_directory) else os.getcwd()

    @property
    def extension(self) -> str:
        name, extension = os.path.splitext(self.source_file)
        return extension

    @property
    def target_file(self) -> str:
        return f'{self.output_directory}/{self.deepl.target_lang.lower()}{self.extension}'

    def check_source_file(self) -> None:
        if not os.path.exists(self.source_file):
            print(f'{colorama.Fore.RED}Error: "{self.source_file}" does not exist!')
            os._exit(0)

    @abstractmethod
    def translate_source_file(self) -> None:
        pass


class TextManager(Manager):

    content: str = ''

    def translate_source_file(self) -> None:
        self.load_source_content()
        self.translate_content()
        if self.content:
            self.make_translated_files()

    def load_source_content(self) -> None:
        try:
            with open(self.source_file, 'r') as source:
                self.content = source.read()
        except:
            print(f'{colorama.Fore.RED}Cannot read {self.extension} files.')
            os._exit(0)

    def translate_content(self) -> None:
        self.content = self.deepl.translate(self.content)

    def make_translated_files(self) -> None:
        with open(self.target_file, 'w+') as destination:
            destination.write(self.content)
            print(f'Generated {self.target_file}.')


class DictionaryManager(TextManager):

    completion_count: int = 0
    not_translated_count: int = 0
    progress_bar: progressbar.ProgressBar
    content: dict = dict()

    def translate_source_file(self) -> None:
        self.load_source_content()
        self.progress_bar = self.get_progress_bar()
        self.translate_content()
        self.print_ending_messages()
        self.make_translated_files()

    def get_progress_bar(self) -> progressbar.ProgressBar:
        number_of_translations: int = self.get_number_of_translations()
        return progressbar.ProgressBar(max_value=number_of_translations, redirect_stdout=True)

    def get_number_of_translations(self) -> int:
        return 0

    def print_ending_messages(self) -> None:
        print('\nTranslation completed.')
        if self.not_translated_count > 0:
            print(
                f'{colorama.Fore.YELLOW}\n{self.not_translated_count} entries have not been translated.\n')

    def translate_and_handle(self, entry: str) -> str:
        translation: str | None = self.deepl.translate(entry)
        if not translation:
            self.not_translated_count += 1
        return translation if translation else entry


class JSONManager(DictionaryManager):

    def get_number_of_translations(self, dictionary: dict[str, str] | None = None) -> int:
        if not dictionary:
            dictionary = self.content
        number: int = 0

        for key, value in dictionary.items():
            number += self.get_number_of_translations(
                value) if isinstance(value, dict) else 1

        return number

    def load_source_content(self) -> None:
        with open(self.source_file, 'r') as source:
            self.content = json.load(source)

    def translate_content(self, dictionary: dict[str, str] | None = None) -> None:

        if not dictionary:
            dictionary = self.content

        for key, value in dictionary.items():

            if isinstance(value, dict):
                self.translate_content(value)

            else:
                dictionary[key] = self.translate_and_handle(value)
                self.completion_count += 1
                self.progress_bar.update(self.completion_count)

    def make_translated_files(self) -> None:
        with open(self.target_file, 'w+') as destination:
            destination.write(json.dumps(self.content, indent=2))
            print(f'Generated {self.target_file}.')


class POManager(DictionaryManager):

    @property
    def pofile_source(self) -> polib.POFile:
        return polib.pofile(self.source_file)

    def get_number_of_translations(self) -> int:
        return len(self.content.items())

    def load_source_content(self) -> None:
        pofile: polib.POFile = self.pofile_source

        for entry in pofile:
            self.content[entry.msgid] = {
                "msgstr": entry.msgid if entry.msgstr == '' else entry.msgstr,
                "occurrences": entry.occurrences
            }

    def translate_content(self) -> None:
        for key, value in self.content.items():
            value['msgstr'] = self.translate_and_handle(value['msgstr'])
            self.completion_count += 1
            self.progress_bar.update(self.completion_count)

    def make_translated_files(self) -> None:
        pofile: polib.POFile = polib.POFile()
        pofile.metadata = self.pofile_source.metadata

        for key, value in self.content.items():
            entry: polib.POEntry = polib.POEntry(
                msgid=key,
                msgstr=value["msgstr"],
                occurrences=value['occurrences']
            )
            pofile.append(entry)

        pofile.save(self.target_file)

        mofile: str = f'{self.output_directory}/{self.deepl.target_lang.lower()}.mo'
        pofile.save_as_mofile(mofile)
        print(f'Generated {self.target_file} and {mofile}.')


class DocumentManager(Manager):

    document_id: str = ''
    document_key: str = ''

    def translate_source_file(self) -> None:
        document_data: dict[str, str] = self.deepl.translate_document(
            self.source_file)
        self.document_id = document_data['document_id']
        self.document_key = document_data['document_key']
        self.download_document_when_ready()

    def download_document_when_ready(self) -> None:
        status_data = self.deepl.check_document_status(
            self.document_id, self.document_key)
        status: str = status_data['status']

        if status == 'done':
            billed_characters: str = status_data['billed_characters']
            print(
                f'Translation completed. Billed characters: {billed_characters}.')
            self.download_target_file()
            return

        # sometimes there are no seconds even if it's still translating
        if 'seconds_remaining' in status_data:
            print(f'Remaining {status_data["seconds_remaining"]} seconds...')

        self.download_document_when_ready()

    def download_target_file(self) -> None:
        binaries: bytes = self.deepl.download_translated_document(
            self.document_id, self.document_key)
        with open(self.target_file, 'wb+') as destination:
            destination.write(binaries)
            print(f'Generated {self.target_file}.')
