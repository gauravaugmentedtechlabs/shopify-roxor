from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from lxml import etree
T = TypeVar("T")

class XmlParser(ABC, Generic[T]):
    """Base class for XML-to-domain parsers."""
    @abstractmethod
    def parse(self, root: etree._Element) -> T:
        """Parse an XML root into a domain object."""
