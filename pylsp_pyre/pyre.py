import dataclasses as dc

import lsprotocol.types as lsp_types


@dc.dataclass
class Location:
    row: int
    column: int


@dc.dataclass
class Check:
    severity: lsp_types.DiagnosticSeverity
    code: str
    message: str
    filename: str
    location: Location
    end_location: Location

