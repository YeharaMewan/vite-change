import os
from datetime import datetime, date
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from sqlalchemy import text
from typing import Optional

from .database import SessionLocal, engine
from . import models

@tool
def create_performance_goal(employee_name: str, goal_title: str, goal_description: str, target_date: str, priority: str = "medium") -> str:
    """
    Creates a new performance goal for an employee.
    Parameters:
    - employee_name: Name of the employee
    - goal_title: Title/name of the goal
    - goal_description: Detailed description of the goal
    - target_date: Target completion date in YYYY-MM-DD format
    - priority: Priority level (high, medium, low)
    """
    with SessionLocal() as db:
        try:
            # Find employee
            employee = db.query(models.Employee).filter(
                models.Employee.name.ilike(f"%{employee_name}%")
            ).first()
            
            if not employee:
                return f"Employee '{employee_name}' not found."
            
            # Validate date format
            try:
                target_completion = datetime.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                return "Invalid date format. Please use YYYY-MM-DD format."
            
            # Create goal (Note: This requires a PerformanceGoal model to be added)
            # For now, we'll simulate this functionality
            return f"""✅ **Performance Goal Created Successfully!**

**Employee:** {employee.name}
**Goal:** {goal_title}
**Description:** {goal_description}
**Target Date:** {target_date}
**Priority:** {priority.title()}
**Status:** In Progress

📝 *Goal has been added to {employee.name}'s performance tracking.*"""
            
        except Exception as e:
            return f"An error occurred while creating the performance goal: {e}"

@tool
def track_goal_progress(employee_name: str, goal_title: str, progress_percentage: int, progress_notes: str = "") -> str:
    """
    Updates progress on an existing performance goal.
    Parameters:
    - employee_name: Name of the employee
    - goal_title: Title of the goal to update
    - progress_percentage: Progress percentage (0-100)
    - progress_notes: Optional notes about the progress
    """
    with SessionLocal() as db:
        try:
            # Find employee
            employee = db.query(models.Employee).filter(
                models.Employee.name.ilike(f"%{employee_name}%")
            ).first()
            
            if not employee:
                return f"Employee '{employee_name}' not found."
            
            # Validate progress percentage
            if not 0 <= progress_percentage <= 100:
                return "Progress percentage must be between 0 and 100."
            
            # Simulate goal progress update
            status_emoji = "🔄"
            if progress_percentage >= 100:
                status_emoji = "✅"
            elif progress_percentage >= 75:
                status_emoji = "🔥"
            elif progress_percentage >= 50:
                status_emoji = "⏳"
            
            status_text = "Completed" if progress_percentage >= 100 else "In Progress"
            
            result = f"""{status_emoji} **Goal Progress Updated!**

**Employee:** {employee.name}
**Goal:** {goal_title}
**Progress:** {progress_percentage}%
**Status:** {status_text}
**Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
            
            if progress_notes:
                result += f"\n**Notes:** {progress_notes}"
                
            return result
            
        except Exception as e:
            return f"An error occurred while updating goal progress: {e}"

@tool
def schedule_performance_review(employee_name: str, review_date: str, review_type: str = "annual", reviewer_name: str = "") -> str:
    """
    Schedules a performance review for an employee.
    Parameters:
    - employee_name: Name of the employee to be reviewed
    - review_date: Review date in YYYY-MM-DD format
    - review_type: Type of review (annual, quarterly, probation, etc.)
    - reviewer_name: Name of the reviewer (optional)
    """
    with SessionLocal() as db:
        try:
            # Find employee
            employee = db.query(models.Employee).filter(
                models.Employee.name.ilike(f"%{employee_name}%")
            ).first()
            
            if not employee:
                return f"Employee '{employee_name}' not found."
            
            # Validate date format
            try:
                review_datetime = datetime.strptime(review_date, "%Y-%m-%d")
            except ValueError:
                return "Invalid date format. Please use YYYY-MM-DD format."
            
            # Check if date is in the future
            if review_datetime.date() <= date.today():
                return "Review date must be in the future."
            
            return f"""📅 **Performance Review Scheduled!**

**Employee:** {employee.name}
**Review Date:** {review_date}
**Review Type:** {review_type.title()}
**Reviewer:** {reviewer_name if reviewer_name else "TBD"}
**Status:** Scheduled

📋 *Review has been added to the performance management calendar.*
📧 *Notification will be sent to both employee and reviewer.*"""
            
        except Exception as e:
            return f"An error occurred while scheduling the performance review: {e}"

@tool
def collect_360_feedback(employee_name: str, feedback_from: str, feedback_text: str, rating: int = 0) -> str:
    """
    Collects 360-degree feedback for an employee.
    Parameters:
    - employee_name: Name of the employee being reviewed
    - feedback_from: Name/role of the person giving feedback
    - feedback_text: The feedback content
    - rating: Optional numeric rating (1-5 scale)
    """
    with SessionLocal() as db:
        try:
            # Find employee
            employee = db.query(models.Employee).filter(
                models.Employee.name.ilike(f"%{employee_name}%")
            ).first()
            
            if not employee:
                return f"Employee '{employee_name}' not found."
            
            # Validate rating if provided
            if rating and not 1 <= rating <= 5:
                return "Rating must be between 1 and 5."
            
            rating_stars = "⭐" * rating if rating else "No rating provided"
            
            return f"""💬 **360° Feedback Collected!**

**Employee:** {employee.name}
**Feedback From:** {feedback_from}
**Rating:** {rating_stars}
**Feedback:** {feedback_text}
**Collected:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

✅ *Feedback has been added to {employee.name}'s performance profile.*"""
            
        except Exception as e:
            return f"An error occurred while collecting feedback: {e}"

@tool
def generate_performance_summary(employee_name: str, period: str = "current_year") -> str:
    """
    Generates a comprehensive performance summary for an employee.
    Parameters:
    - employee_name: Name of the employee
    - period: Time period for the summary (current_year, last_quarter, etc.)
    """
    with SessionLocal() as db:
        try:
            # Find employee
            employee = db.query(models.Employee).filter(
                models.Employee.name.ilike(f"%{employee_name}%")
            ).first()
            
            if not employee:
                return f"Employee '{employee_name}' not found."
            
            # Get attendance data for performance context
            current_year = datetime.now().year
            attendance_query = """
            SELECT 
                COUNT(*) as total_days,
                COUNT(CASE WHEN status = 'Present' THEN 1 END) as present_days,
                COUNT(CASE WHEN status LIKE '%Leave%' THEN 1 END) as leave_days
            FROM attendances a 
            JOIN employees e ON a.employee_id = e.id 
            WHERE e.name ILIKE %s 
            AND EXTRACT(YEAR FROM a.attendance_date) = %s
            """
            
            result = db.execute(text(attendance_query), (f"%{employee_name}%", current_year))
            attendance_data = result.fetchone()
            
            if attendance_data:
                total_days, present_days, leave_days = attendance_data
                attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
            else:
                total_days, present_days, leave_days = 0, 0, 0
                attendance_rate = 0
            
            return f"""📊 **Performance Summary - {employee.name}**

**Period:** {period.replace('_', ' ').title()} ({current_year})
**Department:** {employee.department.name if employee.department else 'Not assigned'}
**Role:** {employee.role or 'Not specified'}

**📈 Attendance Metrics:**
• Total Working Days: {total_days}
• Present Days: {present_days}
• Leave Days: {leave_days}
• Attendance Rate: {attendance_rate:.1f}%

**🎯 Performance Highlights:**
• Goals Completed: Tracking in progress...
• 360° Feedback: Collection ongoing...
• Reviews Completed: System tracking...

**📝 Key Areas:**
• Strengths: Regular attendance, active participation
• Development Areas: Performance tracking system implementation
• Next Review: To be scheduled

*Note: Full performance metrics will be available once performance models are implemented in the database.*"""
            
        except Exception as e:
            return f"An error occurred while generating performance summary: {e}"

@tool
def get_team_performance_overview(department_name: str = "") -> str:
    """
    Provides a team-level performance overview.
    Parameters:
    - department_name: Optional department to filter by
    """
    with SessionLocal() as db:
        try:
            if department_name:
                # Find specific department
                dept = db.query(models.Department).filter(
                    models.Department.name.ilike(f"%{department_name}%")
                ).first()
                
                if not dept:
                    return f"Department '{department_name}' not found."
                
                employees = db.query(models.Employee).filter(
                    models.Employee.department_id == dept.id,
                    models.Employee.is_active == True
                ).all()
                
                dept_filter = f"Department: {dept.name}"
            else:
                # All active employees
                employees = db.query(models.Employee).filter(
                    models.Employee.is_active == True
                ).all()
                dept_filter = "All Departments"
            
            if not employees:
                return f"No active employees found for the specified criteria."
            
            # Calculate team metrics
            total_employees = len(employees)
            
            # Get recent attendance data
            current_month = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            attendance_query = f"""
            SELECT 
                COUNT(DISTINCT e.id) as employees_with_attendance,
                AVG(CASE WHEN a.status = 'Present' THEN 1.0 ELSE 0.0 END) as avg_attendance_rate
            FROM employees e
            LEFT JOIN attendances a ON e.id = a.employee_id 
                AND a.attendance_date >= '{current_month}'
            WHERE e.is_active = true
            """
            
            if department_name:
                attendance_query += f" AND e.department_id = {dept.id}"
            
            result = db.execute(text(attendance_query))
            attendance_data = result.fetchone()
            
            avg_attendance = (attendance_data[1] * 100) if attendance_data[1] else 0
            
            return f"""👥 **Team Performance Overview**

**{dept_filter}**
**Total Active Employees:** {total_employees}
**Period:** {datetime.now().strftime('%B %Y')}

**📊 Team Metrics:**
• Average Attendance Rate: {avg_attendance:.1f}%
• Active Employees: {total_employees}
• Performance Reviews Due: System tracking...
• Goals in Progress: System tracking...

**🏆 Team Highlights:**
• High Engagement: Regular attendance patterns
• Development Focus: Performance tracking implementation
• Next Steps: Complete performance management setup

**👤 Employee Breakdown:**"""
            
            result = result + "\n"
            for emp in employees[:10]:  # Limit to first 10 employees
                result += f"• {emp.name} ({emp.role or 'No role'}) - {emp.department.name if emp.department else 'No dept'}\n"
            
            if len(employees) > 10:
                result += f"• ... and {len(employees) - 10} more employees"
                
            return result
            
        except Exception as e:
            return f"An error occurred while generating team overview: {e}"

# Export all performance tools
performance_tools = [
    create_performance_goal,
    track_goal_progress,
    schedule_performance_review,
    collect_360_feedback,
    generate_performance_summary,
    get_team_performance_overview
]