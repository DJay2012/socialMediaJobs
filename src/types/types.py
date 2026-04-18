from typing import List, TypedDict


class DataMigrationConfigType(TypedDict, total=False):
    """Configuration settings for DataMigration class with flexible setters"""

    source_uri: str
    target_uri: str
    sharded_collections: List[str]
    batch_size: int
    thread_count: int
    retry_attempts: int
    retry_delay: float
