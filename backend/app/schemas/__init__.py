"""
数据校验与序列化 Schema 包
"""
from .user import (
    UserRegisterSchema,
    UserLoginSchema,
    UserUpdateSchema,
    UserChangePasswordSchema,
    UserProfileSchema,
    UserListSchema
)
from .book import (
    BookCreateSchema,
    BookUpdateSchema,
    BookListSchema,
    BookDetailSchema,
    CategoryCreateSchema,
    CategoryUpdateSchema,
    CategorySchema
)
from .borrow import (
    BorrowCreateSchema,
    BorrowListSchema,
    BorrowDetailSchema
)

__all__ = [
    'UserRegisterSchema', 'UserLoginSchema', 'UserUpdateSchema',
    'UserChangePasswordSchema', 'UserProfileSchema', 'UserListSchema',
    'BookCreateSchema', 'BookUpdateSchema', 'BookListSchema', 'BookDetailSchema',
    'CategoryCreateSchema', 'CategoryUpdateSchema', 'CategorySchema',
    'BorrowCreateSchema', 'BorrowListSchema', 'BorrowDetailSchema',
]
