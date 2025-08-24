import os
from datetime import datetime
from langchain_community.vectorstores.pgvector import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain.tools import tool
from dotenv import load_dotenv

from .database import SessionLocal
from . import models

load_dotenv()

@tool
def search_hr_policies(query: str) -> str:
    """
    Searches and retrieves relevant HR policy documents based on a user's query.
    Use this tool for questions about company policies, procedures, guidelines, benefits, etc.
    Examples: 'what is the leave policy?', 'company dress code', 'remote work policy', 'වැඩ කාලය පිළිබදව'.
    """
    connection_string = os.getenv("DATABASE_URL")
    collection_name = "hr_policies"
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    try:
        db = PGVector(
            connection_string=connection_string, 
            embedding_function=embeddings, 
            collection_name=collection_name
        )
        docs = db.similarity_search(query, k=3)
        
        if not docs: 
            return "No relevant HR policy documents found for this query."
            
        context = "Retrieved HR Policy Information:\n\n"
        for i, doc in enumerate(docs, 1):
            document_name = doc.metadata.get('document_name', 'N/A')
            context += f"**{i}. Document: {document_name}**\n"
            context += f"{doc.page_content}\n\n"
            context += "---\n\n"
            
        return context
        
    except Exception as e:
        return f"An error occurred while searching HR policies: {e}"

@tool
def request_leave(employee_name: str, leave_date_str: str, reason: str) -> str:
    """
    Submits a leave request for a specific employee.
    Parameters:
    - employee_name: Name of the employee requesting leave
    - leave_date_str: Leave date in YYYY-MM-DD format
    - reason: Reason for the leave request
    """
    with SessionLocal() as db:
        try:
            # Find employee
            employee = db.query(models.Employee).filter(
                models.Employee.name.ilike(f"%{employee_name}%")
            ).first()
            
            if not employee: 
                return f"Employee '{employee_name}' not found. Cannot submit leave request."
            
            # Validate date format
            try:
                leave_date = datetime.strptime(leave_date_str, "%Y-%m-%d").date()
            except ValueError:
                return "Invalid date format. Please use YYYY-MM-DD format (e.g., 2025-08-25)."
            
            # Check if leave request already exists for this date
            existing_request = db.query(models.LeaveRequest).filter(
                models.LeaveRequest.employee_id == employee.id,
                models.LeaveRequest.leave_date == leave_date
            ).first()
            
            if existing_request:
                return f"A leave request for {employee_name} on {leave_date_str} already exists with status: {existing_request.status}"
            
            # Create new leave request
            leave_request = models.LeaveRequest(
                employee_id=employee.id,
                leave_date=leave_date,
                reason=reason,
                status='pending'
            )
            
            db.add(leave_request)
            db.commit()
            
            return f"✅ Leave request submitted successfully!\n- Employee: {employee.name}\n- Date: {leave_date_str}\n- Reason: {reason}\n- Status: Pending approval"
            
        except Exception as e:
            db.rollback()
            return f"An error occurred while submitting the leave request: {e}"

@tool
def check_leave_status(employee_name: str) -> str:
    """
    Check the status of leave requests for a specific employee.
    Shows all pending, approved, and recent leave requests.
    """
    with SessionLocal() as db:
        try:
            # Find employee
            employee = db.query(models.Employee).filter(
                models.Employee.name.ilike(f"%{employee_name}%")
            ).first()
            
            if not employee:
                return f"Employee '{employee_name}' not found."
            
            # Get all leave requests for this employee
            leave_requests = db.query(models.LeaveRequest).filter(
                models.LeaveRequest.employee_id == employee.id
            ).order_by(models.LeaveRequest.leave_date.desc()).limit(10).all()
            
            if not leave_requests:
                return f"No leave requests found for {employee.name}."
            
            result = f"**Leave Requests for {employee.name}:**\n\n"
            
            for req in leave_requests:
                status_icon = "⏳" if req.status == "pending" else "✅" if req.status == "approved" else "❌"
                result += f"{status_icon} **{req.leave_date}** - {req.status.title()}\n"
                result += f"   Reason: {req.reason}\n\n"
            
            return result
            
        except Exception as e:
            return f"An error occurred while checking leave status: {e}"

@tool
def check_leave_balance(employee_name: str) -> str:
    """
    Check the leave balance for a specific employee.
    Shows total allocated days, used days, and remaining days.
    """
    with SessionLocal() as db:
        try:
            # Find employee
            employee = db.query(models.Employee).filter(
                models.Employee.name.ilike(f"%{employee_name}%")
            ).first()
            
            if not employee:
                return f"Employee '{employee_name}' not found."
            
            # Get current year leave balance
            current_year = datetime.now().year
            leave_balance = db.query(models.LeaveBalance).filter(
                models.LeaveBalance.employee_id == employee.id,
                models.LeaveBalance.year == current_year
            ).first()
            
            if not leave_balance:
                return f"No leave balance information found for {employee.name} in {current_year}."
            
            remaining_days = leave_balance.total_days - leave_balance.days_used
            
            result = f"**Leave Balance for {employee.name} ({current_year}):**\n\n"
            result += f"📅 **Total Allocated Days:** {leave_balance.total_days}\n"
            result += f"📊 **Days Used:** {leave_balance.days_used}\n"
            result += f"🎯 **Remaining Days:** {remaining_days}\n"
            
            if remaining_days <= 5:
                result += f"\n⚠️ **Note:** You have only {remaining_days} leave days remaining."
            
            return result
            
        except Exception as e:
            return f"An error occurred while checking leave balance: {e}"

@tool
def get_company_holidays() -> str:
    """
    Get information about company holidays and important dates.
    This is a placeholder function - you would typically connect this to a holidays database or API.
    """
    # This is a placeholder implementation
    # In a real system, you would fetch this from a database or external API
    holidays_2025 = [
        "New Year's Day - January 1, 2025",
        "Independence Day - February 4, 2025", 
        "Sinhala & Tamil New Year - April 13-14, 2025",
        "Vesak Day - May 12, 2025",
        "Christmas Day - December 25, 2025"
    ]
    
    result = "**Company Holidays 2025:**\n\n"
    for holiday in holidays_2025:
        result += f"🎉 {holiday}\n"
    
    result += "\n📝 **Note:** Additional religious and cultural holidays may apply based on your location."
    
    return result

# Export all policy tools
policy_tools = [
    search_hr_policies,
    request_leave,
    check_leave_status, 
    check_leave_balance,
    get_company_holidays
]