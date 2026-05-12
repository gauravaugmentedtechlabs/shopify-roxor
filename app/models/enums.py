from enum import StrEnum

class ProcessingStatus(StrEnum):
    pending = "pending"
    processing = "processing"
    processed = "processed"
    succeeded = "succeeded"
    failed = "failed"
    dead_letter = "dead_letter"

class FileDirection(StrEnum):
    inbound_from_roxor = "inbound_from_roxor"
    outbound_to_roxor = "outbound_to_roxor"
