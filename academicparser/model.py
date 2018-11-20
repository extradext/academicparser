from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class PaperType(Enum):
    PAPER_TYPE_PMC = 'PMC'
    PAPER_TYPE_ETC = 'ETC'

@dataclass
class ReferenceString:
    ref_string: str = ''
    journal: Optional[str] = None
    volume: Optional[str] = None
    pubmed_path: Optional[str] = None

@dataclass
class Paper:
    type: PaperType
    title: str = ''
    authors: List[str] = field(default_factory=list)
    abstract: str = ''
    references: List[ReferenceString] = field(default_factory=list)
    pmid: Optional[int] = None
    pmcid: Optional[str] = None

