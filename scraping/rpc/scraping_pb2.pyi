import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ScrapeRequest(_message.Message):
    __slots__ = ("entry", "rules")
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    RULES_FIELD_NUMBER: _ClassVar[int]
    entry: str
    rules: ScrapeRules
    def __init__(self, entry: _Optional[str] = ..., rules: _Optional[_Union[ScrapeRules, _Mapping]] = ...) -> None: ...

class ScrapeResponse(_message.Message):
    __slots__ = ("documents",)
    DOCUMENTS_FIELD_NUMBER: _ClassVar[int]
    documents: _containers.RepeatedCompositeFieldContainer[_common_pb2.Document]
    def __init__(self, documents: _Optional[_Iterable[_Union[_common_pb2.Document, _Mapping]]] = ...) -> None: ...

class ScrapeRules(_message.Message):
    __slots__ = ("max_depth", "max_pages", "scrape_patterns", "forbidden_urls")
    MAX_DEPTH_FIELD_NUMBER: _ClassVar[int]
    MAX_PAGES_FIELD_NUMBER: _ClassVar[int]
    SCRAPE_PATTERNS_FIELD_NUMBER: _ClassVar[int]
    FORBIDDEN_URLS_FIELD_NUMBER: _ClassVar[int]
    max_depth: int
    max_pages: int
    scrape_patterns: _containers.RepeatedCompositeFieldContainer[Rule]
    forbidden_urls: _containers.RepeatedCompositeFieldContainer[Regex]
    def __init__(self, max_depth: _Optional[int] = ..., max_pages: _Optional[int] = ..., scrape_patterns: _Optional[_Iterable[_Union[Rule, _Mapping]]] = ..., forbidden_urls: _Optional[_Iterable[_Union[Regex, _Mapping]]] = ...) -> None: ...

class Rule(_message.Message):
    __slots__ = ("url", "css_selector")
    URL_FIELD_NUMBER: _ClassVar[int]
    CSS_SELECTOR_FIELD_NUMBER: _ClassVar[int]
    url: Regex
    css_selector: str
    def __init__(self, url: _Optional[_Union[Regex, _Mapping]] = ..., css_selector: _Optional[str] = ...) -> None: ...

class Regex(_message.Message):
    __slots__ = ("pattern",)
    PATTERN_FIELD_NUMBER: _ClassVar[int]
    pattern: str
    def __init__(self, pattern: _Optional[str] = ...) -> None: ...
