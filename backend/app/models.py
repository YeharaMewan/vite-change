from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from pgvector.sqlalchemy import Vector

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    
    employees = relationship("Employee", back_populates="department")

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    role = Column(String(50))
    department_id = Column(Integer, ForeignKey("departments.id"))
    phone_number = Column(String(50))
    address = Column(Text)
    is_active = Column(Boolean, default=True)

    department = relationship("Department", back_populates="employees")
    attendances = relationship("Attendance", back_populates="employee")
    leave_balances = relationship("LeaveBalance", back_populates="employee")
    leave_requests = relationship("LeaveRequest", back_populates="employee")

class Attendance(Base):
    __tablename__ = "attendances"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    attendance_date = Column(Date, nullable=False)
    status = Column(String(50))
    
    employee = relationship("Employee", back_populates="attendances")

class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    year = Column(Integer, nullable=False)
    total_days = Column(Integer, nullable=False)
    days_used = Column(Integer, nullable=False)
    
    employee = relationship("Employee", back_populates="leave_balances")

class HRPolicy(Base):
    __tablename__ = "hr_policies"
    id = Column(Integer, primary_key=True)
    document_name = Column(String(255), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(1536))

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    leave_date = Column(Date, nullable=False)
    reason = Column(Text)
    status = Column(String(50), default='pending')

    employee = relationship("Employee", back_populates="leave_requests")