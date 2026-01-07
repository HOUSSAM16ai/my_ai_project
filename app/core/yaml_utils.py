from __future__ import annotations

import logging
import os
from typing import Protocol, cast

import yaml

_LOG = logging.getLogger("yaml_utils")

type YamlScalar = str | int | float | bool | None
type YamlValue = YamlScalar | list["YamlValue"] | dict[str, "YamlValue"]
type YamlDocument = dict[str, YamlValue] | list[YamlValue] | YamlValue


class YamlSecurityError(Exception):
    """خطأ أمني يتم إطلاقه عند محاولة تحميل YAML غير آمن."""

    pass


class YamlParser(Protocol):
    """واجهة تحليل YAML صغيرة تضمن عزل تفاصيل المحلل عن المستهلكين."""

    def parse(self, content: str | bytes) -> YamlDocument:
        """يحلل المحتوى ويعيد بنية YAML القياسية."""


class YamlSource(Protocol):
    """واجهة مصدر المحتوى مع حصر المسؤولية بقراءة البيانات فقط."""

    def read(self) -> str | bytes:
        """يعيد المحتوى الخام المطلوب تحليله."""


class SafeYamlParser:
    """محلل YAML آمن يعتمد على `yaml.safe_load` فقط."""

    def parse(self, content: str | bytes) -> YamlDocument:
        """يفسر محتوى YAML باستخدام التحميل الآمن مع حماية من التنفيذ البعيد."""
        try:
            data = yaml.safe_load(content)
            return cast(YamlDocument, data)
        except yaml.YAMLError as exc:
            _LOG.error("فشل تحليل YAML بأمان: %s", exc)
            raise YamlSecurityError(f"Invalid or unsafe YAML content: {exc}") from exc


class YamlFileSource:
    """مصدر ملفات YAML مسؤول فقط عن الوصول للملف وإرجاع المحتوى."""

    def __init__(self, path: str) -> None:
        """يحفظ مسار الملف المطلوب قراءته."""
        self._path = path

    def read(self) -> str:
        """يقرأ محتوى ملف YAML كنص مع التحقق من وجوده."""
        if not os.path.exists(self._path):
            raise FileNotFoundError(f"YAML file not found: {self._path}")
        with open(self._path, encoding="utf-8") as file_handle:
            return file_handle.read()


class YamlStringSource:
    """مصدر YAML يعتمد على نص جاهز دون أي I/O."""

    def __init__(self, content: str | bytes) -> None:
        """يحفظ المحتوى ليتم تمريره للمحلل لاحقًا."""
        self._content = content

    def read(self) -> str | bytes:
        """يعيد المحتوى المحفوظ بدون أي تعديل."""
        return self._content


class YamlLoader:
    """مُنسق تحميل YAML يعتمد على مصدر ومحلل قابلين للحقن."""

    def __init__(self, source: YamlSource, parser: YamlParser) -> None:
        """يبني مسار التحميل بين مصدر المحتوى والمحلل."""
        self._source = source
        self._parser = parser

    def load(self) -> YamlDocument:
        """يحمل المحتوى عبر المصدر ثم يمرره للمحلل."""
        content = self._source.read()
        return self._parser.parse(content)


class YamlParserSelector(Protocol):
    """واجهة خفيفة تضمن أن المستهلك يعتمد فقط على اختيار المحلل."""

    def resolve(self, name: str | None = None) -> YamlParser:
        """يعيد المحلل المناسب وفق الاسم أو الافتراضي."""


class YamlParserRegistry(YamlParserSelector):
    """سجل بسيط لاختيار محول YAML لدعم التمديد دون تعديل النواة."""

    def __init__(self, default_parser: YamlParser) -> None:
        """يبني السجل مع محلل افتراضي واضح."""
        self._default_parser = default_parser
        self._parsers: dict[str, YamlParser] = {}

    def register(self, name: str, parser: YamlParser) -> None:
        """يسجل محللًا جديدًا باسم معرف."""
        self._parsers[name] = parser

    def resolve(self, name: str | None = None) -> YamlParser:
        """يعيد المحلل المسجل أو الافتراضي عند عدم العثور."""
        if name and name in self._parsers:
            return self._parsers[name]
        return self._default_parser


def load_yaml_with_selector(
    content: str | bytes,
    selector: YamlParserSelector,
    parser_name: str | None = None,
) -> YamlDocument:
    """يحمل YAML باستخدام واجهة اختيار صغيرة بدل الاعتماد على سجل كامل."""
    parser = selector.resolve(parser_name)
    return load_yaml(content, parser=parser)


def load_yaml_file_with_selector(
    path: str,
    selector: YamlParserSelector,
    parser_name: str | None = None,
) -> YamlDocument:
    """يحمل ملف YAML باستخدام واجهة اختيار صغيرة."""
    parser = selector.resolve(parser_name)
    return load_yaml_file(path, parser=parser)


def load_yaml(content: str | bytes, parser: YamlParser | None = None) -> YamlDocument:
    """واجهة عامة لتحليل محتوى YAML مع دعم حقن محلل بديل."""
    chosen_parser = parser or SafeYamlParser()
    loader = YamlLoader(YamlStringSource(content), chosen_parser)
    return loader.load()


def load_yaml_file(path: str, parser: YamlParser | None = None) -> YamlDocument:
    """واجهة عامة لتحليل ملف YAML مع دعم حقن محلل بديل."""
    chosen_parser = parser or SafeYamlParser()
    loader = YamlLoader(YamlFileSource(path), chosen_parser)
    return loader.load()


def load_yaml_safely(content: str | bytes) -> YamlDocument:
    """واجهة بسيطة لتحليل محتوى YAML اعتمادًا على المحلل الآمن."""
    return load_yaml(content, parser=SafeYamlParser())


def load_yaml_file_safely(path: str) -> YamlDocument:
    """واجهة بسيطة لقراءة ملف YAML ثم تحليله عبر المحلل الآمن."""
    return load_yaml_file(path, parser=SafeYamlParser())
