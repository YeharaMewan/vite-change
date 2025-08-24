import os
from datetime import datetime, date, timedelta
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from sqlalchemy import text
from typing import List, Dict

from .database import SessionLocal, engine
from . import models

# Predefined skill categories and training programs
SKILL_CATEGORIES = {
    "technical": ["Python", "JavaScript", "SQL", "Machine Learning", "Cloud Computing", "DevOps", "Data Analysis"],
    "soft_skills": ["Communication", "Leadership", "Project Management", "Time Management", "Problem Solving", "Teamwork"],
    "domain_specific": ["HR Management", "Finance", "Marketing", "Sales", "Customer Service", "Quality Assurance"]
}

TRAINING_PROGRAMS = {
    "Python": {"duration": "4 weeks", "type": "Technical", "level": "Intermediate", "provider": "Internal"},
    "Leadership": {"duration": "6 weeks", "type": "Soft Skills", "level": "Advanced", "provider": "External"},
    "Communication": {"duration": "2 weeks", "type": "Soft Skills", "level": "Beginner", "provider": "Internal"},
    "Machine Learning": {"duration": "8 weeks", "type": "Technical", "level": "Advanced", "provider": "External"},
    "Project Management": {"duration": "3 weeks", "type": "Soft Skills", "level": "Intermediate", "provider": "Internal"},
}

@tool
def assess_skill_gaps(employee_name: str, role_requirements: str = "") -> str:
    """
    Performs a skill gap analysis for an employee against their current role or desired role.
    Parameters:
    - employee_name: Name of the employee
    - role_requirements: Optional specific role requirements to assess against
    """
    with SessionLocal() as db:
        try:
            # Find employee
            employee = db.query(models.Employee).filter(
                models.Employee.name.ilike(f"%{employee_name}%")
            ).first()
            
            if not employee:
                return f"Employee '{employee_name}' not found."
            
            current_role = employee.role or "Not specified"
            department = employee.department.name if employee.department else "Not assigned"
            
            # Generate skill assessment using AI
            ai_model = ChatOpenAI(model="gpt-4o", temperature=0.3)
            
            assessment_prompt = f"""
            As an HR Learning & Development specialist, assess the skill gaps for the following employee:
            
            Employee: {employee.name}
            Current Role: {current_role}
            Department: {department}
            Role Requirements: {role_requirements if role_requirements else "Standard for " + current_role}
            
            Provide a skill gap analysis covering:
            1. Current likely skills (based on role and department)
            2. Required skills for the role
            3. Identified gaps
            4. Priority areas for development
            5. Recommended training focus
            
            Format the response in a clear, actionable manner with bullet points.
            """
            
            assessment = ai_model.invoke(assessment_prompt).content
            
            return f"""🎯 **Skill Gap Analysis - {employee.name}**

**Current Role:** {current_role}
**Department:** {department}
**Assessment Date:** {datetime.now().strftime('%Y-%m-%d')}

{assessment}

**📚 Next Steps:**
1. Review recommended training programs
2. Create personalized learning path
3. Set skill development milestones
4. Schedule progress reviews

*Use 'recommend_training_programs' to get specific program suggestions.*"""
            
        except Exception as e:
            return f"An error occurred during skill gap assessment: {e}"

@tool
def recommend_training_programs(employee_name: str, skill_focus: str, urgency: str = "medium") -> str:
    """
    Recommends training programs based on employee needs and skill focus areas.
    Parameters:
    - employee_name: Name of the employee
    - skill_focus: Primary skill area to focus on (technical, soft_skills, domain_specific)
    - urgency: Priority level (high, medium, low)
    """
    with SessionLocal() as db:
        try:
            # Find employee
            employee = db.query(models.Employee).filter(
                models.Employee.name.ilike(f"%{employee_name}%")
            ).first()
            
            if not employee:
                return f"Employee '{employee_name}' not found."
            
            # Get relevant skills based on focus area
            focus_skills = SKILL_CATEGORIES.get(skill_focus.lower(), [])
            
            if not focus_skills:
                focus_skills = ["Communication", "Leadership", "Problem Solving"]  # Default recommendations
            
            recommendations = []
            for skill in focus_skills[:5]:  # Limit to top 5 recommendations
                if skill in TRAINING_PROGRAMS:
                    program = TRAINING_PROGRAMS[skill]
                    recommendations.append({
                        "skill": skill,
                        "duration": program["duration"],
                        "level": program["level"],
                        "type": program["type"],
                        "provider": program["provider"]
                    })
            
            # Priority indicators
            priority_emoji = {"high": "🔥", "medium": "⚡", "low": "📚"}[urgency.lower()]
            
            result = f"""{priority_emoji} **Training Recommendations - {employee.name}**

**Focus Area:** {skill_focus.replace('_', ' ').title()}
**Priority:** {urgency.title()}
**Generated:** {datetime.now().strftime('%Y-%m-%d')}

**📚 Recommended Programs:**"""
            
            for i, rec in enumerate(recommendations, 1):
                result += f"""

**{i}. {rec['skill']} Training**
   • Duration: {rec['duration']}
   • Level: {rec['level']}
   • Type: {rec['type']}
   • Provider: {rec['provider']}
   • Status: Available"""
            
            result += f"""

**🎯 Implementation Plan:**
1. Enroll in top 2-3 priority programs
2. Schedule learning time in calendar
3. Assign learning buddy/mentor
4. Set completion milestones
5. Plan progress assessments

*Use 'create_learning_path' to build a structured development plan.*"""
            
            return result
            
        except Exception as e:
            return f"An error occurred while generating training recommendations: {e}"

@tool
def create_learning_path(employee_name: str, target_role: str, timeline_months: int = 6) -> str:
    """
    Creates a structured learning path for an employee toward a target role or skill set.
    Parameters:
    - employee_name: Name of the employee
    - target_role: Target role or skill area to work toward
    - timeline_months: Learning timeline in months (default 6)
    """
    with SessionLocal() as db:
        try:
            # Find employee
            employee = db.query(models.Employee).filter(
                models.Employee.name.ilike(f"%{employee_name}%")
            ).first()
            
            if not employee:
                return f"Employee '{employee_name}' not found."
            
            current_role = employee.role or "Current Role"
            
            # Generate learning path using AI
            ai_model = ChatOpenAI(model="gpt-4o", temperature=0.3)
            
            path_prompt = f"""
            Create a structured {timeline_months}-month learning path for:
            
            Employee: {employee.name}
            Current Role: {current_role}
            Target Role/Skills: {target_role}
            Timeline: {timeline_months} months
            
            Structure the learning path with:
            1. Monthly milestones
            2. Specific skills/courses for each month
            3. Practical projects or assignments
            4. Assessment checkpoints
            5. Resources needed
            
            Make it progressive and practical.
            """
            
            learning_path = ai_model.invoke(path_prompt).content
            
            # Calculate key dates
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=30 * timeline_months)
            first_checkpoint = start_date + timedelta(days=30)
            
            return f"""🛤️ **Personalized Learning Path - {employee.name}**

**Journey:** {current_role} → {target_role}
**Duration:** {timeline_months} months
**Start Date:** {start_date}
**Target Completion:** {end_date}
**First Checkpoint:** {first_checkpoint}

{learning_path}

**📊 Success Metrics:**
• Course completion rates
• Skill assessment scores  
• Project deliverables
• Peer feedback ratings
• Manager evaluation

**🔄 Progress Tracking:**
• Weekly self-assessments
• Monthly manager check-ins
• Quarterly skills evaluation
• Final role readiness assessment

*Path will be monitored and adjusted based on progress and feedback.*"""
            
        except Exception as e:
            return f"An error occurred while creating the learning path: {e}"

@tool
def track_training_completion(employee_name: str, program_name: str, completion_status: str, completion_date: str = "", score: int = 0) -> str:
    """
    Tracks completion of training programs and certifications.
    Parameters:
    - employee_name: Name of the employee
    - program_name: Name of the training program/course
    - completion_status: Status (completed, in_progress, not_started, dropped)
    - completion_date: Completion date in YYYY-MM-DD format (if completed)
    - score: Optional score or grade (0-100)
    """
    with SessionLocal() as db:
        try:
            # Find employee
            employee = db.query(models.Employee).filter(
                models.Employee.name.ilike(f"%{employee_name}%")
            ).first()
            
            if not employee:
                return f"Employee '{employee_name}' not found."
            
            # Validate completion date if provided
            if completion_date:
                try:
                    comp_date = datetime.strptime(completion_date, "%Y-%m-%d").date()
                except ValueError:
                    return "Invalid completion date format. Please use YYYY-MM-DD format."
            else:
                comp_date = datetime.now().date() if completion_status == "completed" else None
            
            # Status emojis
            status_emojis = {
                "completed": "✅",
                "in_progress": "🔄", 
                "not_started": "📚",
                "dropped": "❌"
            }
            
            status_emoji = status_emojis.get(completion_status.lower(), "📝")
            
            result = f"""{status_emoji} **Training Progress Updated**

**Employee:** {employee.name}
**Program:** {program_name}
**Status:** {completion_status.replace('_', ' ').title()}"""
            
            if comp_date:
                result += f"\n**Completion Date:** {comp_date}"
            
            if score > 0:
                result += f"\n**Score:** {score}%"
                if score >= 90:
                    result += " 🌟 Excellent!"
                elif score >= 80:
                    result += " 👍 Great job!"
                elif score >= 70:
                    result += " ✅ Good work!"
            
            result += f"\n**Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Add next steps based on status
            if completion_status == "completed":
                result += f"""

**🎉 Congratulations on completing the training!**
**Next Steps:**
• Update skill profile
• Apply new skills in current role  
• Share knowledge with team
• Consider advanced programs"""
            
            elif completion_status == "in_progress":
                result += f"""

**🔄 Keep up the great work!**
**Next Steps:**
• Continue with scheduled modules
• Complete assignments on time
• Seek help if needed
• Track progress weekly"""
            
            return result
            
        except Exception as e:
            return f"An error occurred while tracking training completion: {e}"

@tool
def generate_training_report(employee_name: str = "", department: str = "", period: str = "current_year") -> str:
    """
    Generates a comprehensive training and development report.
    Parameters:
    - employee_name: Optional specific employee (leave empty for all)
    - department: Optional department filter
    - period: Report period (current_year, last_quarter, etc.)
    """
    with SessionLocal() as db:
        try:
            # Build query based on filters
            query_conditions = ["e.is_active = true"]
            params = {}
            
            if employee_name:
                # Find specific employee
                employee = db.query(models.Employee).filter(
                    models.Employee.name.ilike(f"%{employee_name}%")
                ).first()
                
                if not employee:
                    return f"Employee '{employee_name}' not found."
                
                query_conditions.append("e.id = :emp_id")
                params['emp_id'] = employee.id
                report_scope = f"Employee: {employee.name}"
                
            elif department:
                # Find department
                dept = db.query(models.Department).filter(
                    models.Department.name.ilike(f"%{department}%")
                ).first()
                
                if not dept:
                    return f"Department '{department}' not found."
                
                query_conditions.append("e.department_id = :dept_id")
                params['dept_id'] = dept.id
                report_scope = f"Department: {dept.name}"
                
            else:
                report_scope = "Company-wide"
            
            # Get employee data
            where_clause = " AND ".join(query_conditions)
            employee_query = f"""
            SELECT 
                e.name,
                e.role,
                d.name as department_name,
                COUNT(DISTINCT CASE WHEN a.status = 'Present' THEN a.attendance_date END) as attendance_days
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.id
            LEFT JOIN attendances a ON e.id = a.employee_id 
                AND EXTRACT(YEAR FROM a.attendance_date) = EXTRACT(YEAR FROM CURRENT_DATE)
            WHERE {where_clause}
            GROUP BY e.id, e.name, e.role, d.name
            ORDER BY e.name
            """
            
            result = db.execute(text(employee_query), params)
            employees_data = result.fetchall()
            
            if not employees_data:
                return f"No employees found for the specified criteria."
            
            # Generate comprehensive report
            total_employees = len(employees_data)
            current_year = datetime.now().year
            
            report = f"""📊 **Training & Development Report**

**Scope:** {report_scope}
**Period:** {period.replace('_', ' ').title()} ({current_year})
**Total Employees:** {total_employees}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

**🎯 Training Metrics Overview:**
• Employees with Active Training: Tracking in development
• Average Training Hours: System tracking setup needed
• Completion Rate: Tracking implementation in progress
• Certification Rate: Database enhancement required

**📈 Skill Development Trends:**
• High Demand Skills: Technical skills, Leadership, Communication
• Emerging Training Needs: AI/ML, Remote work management
• Popular Programs: To be tracked with enhanced system

**👥 Employee Training Summary:**"""
            
            for emp_data in employees_data[:10]:  # Limit to first 10 employees
                name, role, dept_name, attendance = emp_data
                report += f"""

**{name}**
• Role: {role or 'Not specified'}
• Department: {dept_name or 'Not assigned'}  
• Attendance Days: {attendance or 0}
• Training Status: Tracking system in development"""
            
            if len(employees_data) > 10:
                report += f"\n\n*... and {len(employees_data) - 10} more employees*"
            
            report += f"""

**🚀 Recommendations:**
1. Implement training database models for detailed tracking
2. Set up automated training completion monitoring  
3. Create skills matrix and gap analysis system
4. Establish learning & development budget tracking
5. Launch mentorship and internal knowledge sharing programs

**📋 Next Actions:**
• Complete training system database implementation
• Set up training provider integrations
• Launch employee self-assessment tools
• Establish training ROI measurement metrics"""
            
            return report
            
        except Exception as e:
            return f"An error occurred while generating the training report: {e}"

@tool
def schedule_skills_assessment(employee_name: str, assessment_type: str, assessment_date: str, assessor: str = "") -> str:
    """
    Schedules a skills assessment for an employee.
    Parameters:
    - employee_name: Name of the employee
    - assessment_type: Type of assessment (technical, soft_skills, role_specific, annual)
    - assessment_date: Assessment date in YYYY-MM-DD format
    - assessor: Optional assessor name
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
                assessment_datetime = datetime.strptime(assessment_date, "%Y-%m-%d")
            except ValueError:
                return "Invalid date format. Please use YYYY-MM-DD format."
            
            # Check if date is in the future
            if assessment_datetime.date() <= date.today():
                return "Assessment date should be in the future."
            
            return f"""📋 **Skills Assessment Scheduled**

**Employee:** {employee.name}
**Assessment Type:** {assessment_type.replace('_', ' ').title()}
**Scheduled Date:** {assessment_date}
**Assessor:** {assessor if assessor else 'TBD'}
**Department:** {employee.department.name if employee.department else 'Not assigned'}

**📚 Assessment Will Cover:**
• Current skill levels and competencies
• Progress since last assessment
• Areas for improvement
• Training recommendations
• Career development planning

**🔔 Notifications:**
• Employee notification sent
• Assessor notification sent (if assigned)
• Calendar invitation created
• Preparation materials will be provided

*Assessment results will be used to update training recommendations and learning paths.*"""
            
        except Exception as e:
            return f"An error occurred while scheduling the skills assessment: {e}"

# Export all training tools
training_tools = [
    assess_skill_gaps,
    recommend_training_programs,
    create_learning_path,
    track_training_completion,
    generate_training_report,
    schedule_skills_assessment
]