import enum

class UserRole(str, enum.Enum):
    SELLER = "SELLER"
    BUYER = "BUYER"
    ADMIN = "ADMIN"

class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    BANNED = "BANNED"

class IdeaStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"

class DealStatus(str, enum.Enum):
    OFFERED = "OFFERED"
    ESCROWED = "ESCROWED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
