import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass

from polyglot import license

ACTIONS: list[str] = [
    "translate",
    "set_license",
    "print_supported_languages",
    "print_usage_info",
]


@dataclass
class Arguments:
    action: str
    source_file: str
    target_lang: str
    output_directory: str
    source_lang: str
    license_manager: license.LicenseManager


class ArgumentsCollector(ABC):
    arguments: Arguments

    def __init__(self) -> None:
        self._collect_arguments()
        self._validate_arguments()

    @abstractmethod
    def _collect_arguments() -> None:
        pass

    @abstractmethod
    def _validate_arguments() -> None:
        pass


class CLIArgumentsCollector(ArgumentsCollector):

    __parser: argparse.ArgumentParser
    __namespace: argparse.Namespace

    def _collect_arguments(self) -> None:
        self.__set_parser()
        self.__namespace = self.__parser.parse_args()
        self.arguments = Arguments(
            action=self.__namespace.action,
            source_file=self.__namespace.source_file,
            target_lang=self.__namespace.target_lang,
            output_directory=self.__namespace.output_directory,
            source_lang=self.__namespace.source_lang,
            license_manager=license.CLILicenseManager(),
        )

    def _validate_arguments(self) -> None:
        if self.__namespace.action == "translate" and (
            self.__namespace.source_file == "" or self.__namespace.target_lang == ""
        ):
            self.__parser.error("translate requires --source_file and --target_lang.")

    def __set_parser(self) -> None:

        parser: argparse.ArgumentParser = argparse.ArgumentParser(
            description="Polyglot will translate the given files."
        )

        parser.add_argument(
            "action",
            type=str,
            help="The command that will be exectued. The following options are for the translate command.",
            choices=ACTIONS,
        )

        parser.add_argument(
            "-p",
            "--source_file",
            type=str,
            help='The file to be translated. Required if the action is "translate."',
            default="",
        )

        parser.add_argument(
            "-t",
            "--target_lang",
            type=str,
            help='The code of the language into which you want to translate the source file. Required if the action is "translate".',
            default="",
        )

        parser.add_argument(
            "-o",
            "--output_directory",
            type=str,
            help="The directory where the output file will be located. Will be used the working directory if this option is invalid or not used.",
            default="",
        )

        parser.add_argument(
            "-s",
            "--source_lang",
            type=str,
            help="Source file language code. Detected automatically by DeepL by default. Specifying it can increase performance and make translations more accurate.",
            default="",
        )
        self.__parser = parser
