from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.dialects.mysql import INTEGER as MySqlInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(
        Integer().with_variant(MySqlInteger(unsigned=True), "mysql"),
        primary_key=True,
        autoincrement=True,
    )
    dataset_id: Mapped[int] = mapped_column(
        Integer().with_variant(MySqlInteger(unsigned=True), "mysql"),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False)
    result_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    dataset: Mapped["Dataset"] = relationship(back_populates="analysis_results")


from app.models.dataset import Dataset  # noqa: E402
