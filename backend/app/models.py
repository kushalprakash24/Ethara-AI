import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    role = Column(String, default="employee")  # admin, hr, pm, employee
    joining_date = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    allocation = relationship("SeatAllocation", uselist=False, back_populates="employee")

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)

    # Relationships
    allocations = relationship("SeatAllocation", back_populates="project")

class Floor(Base):
    __tablename__ = "floors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    floor_number = Column(Integer, nullable=False)
    block_name = Column(String, nullable=False)

    seats = relationship("Seat", back_populates="floor", cascade="all, delete-orphan")

class Seat(Base):
    __tablename__ = "seats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seat_number = Column(String, nullable=False, unique=True)
    floor_id = Column(UUID(as_uuid=True), ForeignKey("floors.id"), nullable=False)
    status = Column(String, default="vacant")  # vacant, occupied, reserved

    # Relationships
    floor = relationship("Floor", back_populates="seats")
    allocation = relationship("SeatAllocation", uselist=False, back_populates="seat")

class SeatAllocation(Base):
    __tablename__ = "seat_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), unique=True, nullable=False)
    seat_id = Column(UUID(as_uuid=True), ForeignKey("seats.id"), unique=True, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    allocated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="allocation")
    seat = relationship("Seat", back_populates="allocation")
    project = relationship("Project", back_populates="allocations")