from typing import Any, Sequence

import sqlalchemy as sa
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

import models
from core.security import hash_password


faker = Faker()


class MainFactory:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.data: list[dict] = []
        self.model: models.TypeModel | None = None

    async def generate_data(self, count: int = 1, **kwargs):
        """
        Генерация данных для фабрики
        """
        raise NotImplementedError("Нужна реализация")

    async def insert_to_db(self) -> None:
        """
        Запись данных в БД
        """
        stmt = sa.insert(self.model).values(self.data)  # type:ignore[arg-type]
        await self.session.execute(stmt)

    async def get_data(self) -> Sequence[Any]:
        """
        Получение данных из БД
        """
        stmt = sa.select(self.model)  # type:ignore[arg-type]
        result = await self.session.scalars(stmt)
        return result.unique().all()


class UserFactory(MainFactory):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.model = models.User

    async def generate_data(
        self, count: int = 1, **kwargs
    ) -> Sequence[models.User]:
        self.data.extend(
            {
                "email": kwargs.get("email", faker.email()),
                "password": hash_password(
                    kwargs.get("password", faker.password())
                ),
                "name": kwargs.get("name", faker.first_name()),
                "phone": kwargs.get("phone", faker.phone_number()),
                "status": kwargs.get("status", models.UserStatus.BUYER),
            }
            for _ in range(count)
        )

        await self.insert_to_db()
        await self.session.commit()
        return await self.get_data()
