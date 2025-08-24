import os
from datetime import datetime, date, timedelta
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from sqlalchemy import text, func
from typing import Dict, List
import json

from .database import SessionLocal, engine
from . import models

@tool
def generate_hr_dashboard_metrics(period: str = "current_month") -> str:
    """
    Generates key HR metrics for the dashboard.
    Parameters:
    - period: Time period for metrics (current_month, current_quarter, current_year, last_month)
    """
    with SessionLocal() as db:
        try:
            current_date = datetime.now()
            
            # Define date ranges based on period
            if period == "current_month":
                start_date = current_date.replace(day=1).date()
                end_date = current_date.date()
                period_label = current_date.strftime("%B %Y")
            elif period == "current_quarter":
                quarter = ((current_date.month - 1) // 3) + 1
                start_date = datetime(current_date.year, (quarter-1)*3 + 1, 1).date()
                end_date = current_date.date()
                period_label = f"Q{quarter} {current_date.year}"
            elif period == "current_year":
                start_date = datetime(current_date.year, 1, 1).date()
                end_date = current_date.date()
                period_label = str(current_date.year)
            elif period == "last_month":
                last_month = current_date.replace(day=1) - timedelta(days=1)
                start_date = last_month.replace(day=1).date()
                end_date = last_month.date()
                period_label = last_month.strftime("%B %Y")
            else:
                start_date = current_date.replace(day=1).date()
                end_date = current_date.date()
                period_label = current_date.strftime("%B %Y")
            
            # Employee Metrics
            total_employees = db.query(models.Employee).filter(models.Employee.is_active == True).count()
            total_departments = db.query(models.Department).count()
            
            # Attendance Metrics
            attendance_query = text("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN status = 'Present' THEN 1 END) as present_count,
                    COUNT(CASE WHEN status LIKE '%Leave%' THEN 1 END) as leave_count,
                    COUNT(CASE WHEN status = 'Absent' THEN 1 END) as absent_count
                FROM attendances 
                WHERE attendance_date BETWEEN :start_date AND :end_date
            """)
            
            attendance_result = db.execute(attendance_query, {
                'start_date': start_date, 
                'end_date': end_date
            }).fetchone()
            
            if attendance_result:
                total_records, present_count, leave_count, absent_count = attendance_result
                attendance_rate = (present_count / total_records * 100) if total_records > 0 else 0
                leave_rate = (leave_count / total_records * 100) if total_records > 0 else 0
                absent_rate = (absent_count / total_records * 100) if total_records > 0 else 0
            else:
                total_records = present_count = leave_count = absent_count = 0
                attendance_rate = leave_rate = absent_rate = 0
            
            # Leave Requests Metrics
            leave_requests = db.query(models.LeaveRequest).filter(
                models.LeaveRequest.leave_date.between(start_date, end_date)
            ).count()
            
            pending_leaves = db.query(models.LeaveRequest).filter(
                models.LeaveRequest.leave_date.between(start_date, end_date),
                models.LeaveRequest.status == 'pending'
            ).count()
            
            # Department Breakdown
            dept_query = text("""
                SELECT 
                    d.name,
                    COUNT(e.id) as employee_count,
                    AVG(CASE WHEN a.status = 'Present' THEN 1.0 ELSE 0.0 END) * 100 as dept_attendance_rate
                FROM departments d
                LEFT JOIN employees e ON d.id = e.department_id AND e.is_active = true
                LEFT JOIN attendances a ON e.id = a.employee_id 
                    AND a.attendance_date BETWEEN :start_date AND :end_date
                GROUP BY d.id, d.name
                ORDER BY employee_count DESC
            """)
            
            dept_result = db.execute(dept_query, {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            return f"""📊 **HR Analytics Dashboard**

**Period:** {period_label}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

**👥 WORKFORCE OVERVIEW**
• Total Active Employees: {total_employees}
• Total Departments: {total_departments}
• Average Team Size: {total_employees // total_departments if total_departments > 0 else 0}

**📈 ATTENDANCE METRICS**
• Overall Attendance Rate: {attendance_rate:.1f}%
• Leave Rate: {leave_rate:.1f}%
• Absence Rate: {absent_rate:.1f}%
• Total Attendance Records: {total_records}

**📋 LEAVE MANAGEMENT**
• Total Leave Requests: {leave_requests}
• Pending Approvals: {pending_leaves}
• Approval Rate: {((leave_requests - pending_leaves) / leave_requests * 100) if leave_requests > 0 else 0:.1f}%

**🏢 DEPARTMENT BREAKDOWN**"""
            
            result = result if 'result' in locals() else ""
            
            for dept_name, emp_count, dept_attendance in dept_result[:5]:  # Top 5 departments
                dept_attendance = dept_attendance or 0
                result += f"""
• **{dept_name}**: {emp_count} employees | {dept_attendance:.1f}% attendance"""
            
            result += f"""

**🎯 KEY INSIGHTS**
• {'High' if attendance_rate >= 85 else 'Moderate' if attendance_rate >= 75 else 'Low'} attendance rate overall
• {'Efficient' if pending_leaves <= 5 else 'Review needed'} leave approval process
• {'Well-distributed' if total_departments >= 3 else 'Centralized'} workforce structure

**📊 TRENDING METRICS**
• Attendance: {'↗️ Improving' if attendance_rate >= 80 else '→ Stable' if attendance_rate >= 70 else '↘️ Needs attention'}
• Leave Management: {'✅ Efficient' if pending_leaves <= 10 else '⚠️ Backlog present'}
• Workforce: {'📈 Growing' if total_employees >= 10 else '🔄 Stable'}"""
            
            return result
            
        except Exception as e:
            return f"An error occurred while generating HR dashboard metrics: {e}"

@tool
def analyze_attendance_patterns(employee_name: str = "", department: str = "", days_back: int = 30) -> str:
    """
    Analyzes attendance patterns and trends for individuals, departments, or the entire organization.
    Parameters:
    - employee_name: Optional specific employee to analyze
    - department: Optional department to analyze
    - days_back: Number of days to look back for analysis (default 30)
    """
    with SessionLocal() as db:
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            # Build query based on filters
            base_query = """
                SELECT 
                    e.name,
                    d.name as department_name,
                    a.attendance_date,
                    a.status,
                    EXTRACT(DOW FROM a.attendance_date) as day_of_week
                FROM attendances a
                JOIN employees e ON a.employee_id = e.id
                LEFT JOIN departments d ON e.department_id = d.id
                WHERE a.attendance_date BETWEEN :start_date AND :end_date
            """
            
            params = {'start_date': start_date, 'end_date': end_date}
            
            if employee_name:
                base_query += " AND e.name ILIKE :employee_name"
                params['employee_name'] = f"%{employee_name}%"
                analysis_scope = f"Employee: {employee_name}"
            elif department:
                base_query += " AND d.name ILIKE :department"
                params['department'] = f"%{department}%"
                analysis_scope = f"Department: {department}"
            else:
                analysis_scope = "Organization-wide"
            
            base_query += " ORDER BY a.attendance_date DESC"
            
            result = db.execute(text(base_query), params)
            attendance_data = result.fetchall()
            
            if not attendance_data:
                return f"No attendance data found for {analysis_scope} in the last {days_back} days."
            
            # Analyze patterns
            total_records = len(attendance_data)
            present_count = sum(1 for record in attendance_data if record[3] == 'Present')
            leave_count = sum(1 for record in attendance_data if 'Leave' in record[3])
            absent_count = sum(1 for record in attendance_data if record[3] == 'Absent')
            
            # Day of week analysis
            day_patterns = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
            day_attendance = {}
            
            for record in attendance_data:
                day = int(record[4])  # day_of_week
                status = record[3]
                if day not in day_attendance:
                    day_attendance[day] = {'Present': 0, 'Leave': 0, 'Absent': 0, 'Total': 0}
                
                day_attendance[day]['Total'] += 1
                if status == 'Present':
                    day_attendance[day]['Present'] += 1
                elif 'Leave' in status:
                    day_attendance[day]['Leave'] += 1
                elif status == 'Absent':
                    day_attendance[day]['Absent'] += 1
            
            return f"""📊 **Attendance Pattern Analysis**

**Scope:** {analysis_scope}
**Period:** {start_date} to {end_date} ({days_back} days)
**Total Records:** {total_records}

**📈 Overall Attendance Metrics:**
• Present: {present_count} ({present_count/total_records*100:.1f}%)
• On Leave: {leave_count} ({leave_count/total_records*100:.1f}%)
• Absent: {absent_count} ({absent_count/total_records*100:.1f}%)

**📅 Day-of-Week Patterns:**"""
            
            result = result if 'result' in locals() else ""
            
            for day_num in sorted(day_attendance.keys()):
                if day_num < 5:  # Weekdays only
                    day_data = day_attendance[day_num]
                    present_rate = (day_data['Present'] / day_data['Total'] * 100) if day_data['Total'] > 0 else 0
                    result += f"""
• **{day_patterns[day_num]}**: {present_rate:.1f}% attendance ({day_data['Present']}/{day_data['Total']})"""
            
            # Identify trends
            recent_week = [record for record in attendance_data if record[2] >= (end_date - timedelta(days=7))]
            recent_present = sum(1 for record in recent_week if record[3] == 'Present')
            recent_rate = (recent_present / len(recent_week) * 100) if recent_week else 0
            
            overall_rate = present_count / total_records * 100
            
            result += f"""

**🔍 Pattern Insights:**
• Recent Week Attendance: {recent_rate:.1f}%
• Overall Period Average: {overall_rate:.1f}%
• Trend: {'↗️ Improving' if recent_rate > overall_rate else '↘️ Declining' if recent_rate < overall_rate - 5 else '→ Stable'}

**⚠️ Recommendations:**"""
            
            if overall_rate < 75:
                result += """
• Investigate attendance issues and root causes
• Review workload and work-life balance
• Consider flexible work arrangements"""
            elif overall_rate < 85:
                result += """
• Monitor attendance trends closely
• Provide additional support where needed
• Recognize good attendance performers"""
            else:
                result += """
• Maintain current attendance standards
• Continue recognizing excellent attendance
• Share best practices across teams"""
            
            return result
            
        except Exception as e:
            return f"An error occurred during attendance pattern analysis: {e}"

@tool
def predict_employee_turnover_risk(lookback_months: int = 6) -> str:
    """
    Analyzes employee data to predict turnover risk using various factors.
    Parameters:
    - lookback_months: Number of months to analyze for patterns (default 6)
    """
    with SessionLocal() as db:
        try:
            current_date = datetime.now()
            analysis_start = current_date - timedelta(days=30 * lookback_months)
            
            # Get employee metrics for risk analysis
            risk_analysis_query = text("""
                SELECT 
                    e.id,
                    e.name,
                    e.role,
                    d.name as department_name,
                    e.is_active,
                    COUNT(DISTINCT a.attendance_date) as total_attendance_days,
                    COUNT(DISTINCT CASE WHEN a.status = 'Present' THEN a.attendance_date END) as present_days,
                    COUNT(DISTINCT CASE WHEN a.status = 'Absent' THEN a.attendance_date END) as absent_days,
                    COUNT(DISTINCT lr.id) as leave_requests,
                    COUNT(DISTINCT CASE WHEN lr.status = 'pending' THEN lr.id END) as pending_leaves
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                LEFT JOIN attendances a ON e.id = a.employee_id 
                    AND a.attendance_date >= :analysis_start
                LEFT JOIN leave_requests lr ON e.id = lr.employee_id 
                    AND lr.leave_date >= :analysis_start
                WHERE e.is_active = true
                GROUP BY e.id, e.name, e.role, d.name, e.is_active
                ORDER BY e.name
            """)
            
            result = db.execute(risk_analysis_query, {'analysis_start': analysis_start.date()})
            employee_data = result.fetchall()
            
            if not employee_data:
                return "No employee data available for turnover risk analysis."
            
            # Analyze risk factors for each employee
            risk_employees = []
            low_risk_employees = []
            
            for emp_data in employee_data:
                (emp_id, name, role, dept_name, is_active, 
                 total_attendance, present_days, absent_days, 
                 leave_requests, pending_leaves) = emp_data
                
                # Calculate risk score (0-100, higher = more risk)
                risk_score = 0
                risk_factors = []
                
                # Attendance risk factors
                if total_attendance > 0:
                    attendance_rate = present_days / total_attendance
                    if attendance_rate < 0.7:
                        risk_score += 30
                        risk_factors.append("Low attendance rate")
                    elif attendance_rate < 0.8:
                        risk_score += 15
                        risk_factors.append("Moderate attendance concerns")
                
                # Absence patterns
                if absent_days > 10:
                    risk_score += 20
                    risk_factors.append("High absence frequency")
                
                # Leave request patterns  
                if leave_requests > 8:
                    risk_score += 15
                    risk_factors.append("Frequent leave requests")
                
                if pending_leaves > 3:
                    risk_score += 10
                    risk_factors.append("Multiple pending leave requests")
                
                # Department risk (some departments may have higher turnover)
                if not dept_name:
                    risk_score += 5
                    risk_factors.append("No department assignment")
                
                # Role risk
                if not role:
                    risk_score += 5
                    risk_factors.append("Undefined role")
                
                employee_risk = {
                    'name': name,
                    'role': role or 'Not specified',
                    'department': dept_name or 'Not assigned',
                    'risk_score': risk_score,
                    'risk_factors': risk_factors,
                    'attendance_rate': (present_days / total_attendance * 100) if total_attendance > 0 else 0
                }
                
                if risk_score >= 40:
                    risk_employees.append(employee_risk)
                else:
                    low_risk_employees.append(employee_risk)
            
            # Sort by risk score
            risk_employees.sort(key=lambda x: x['risk_score'], reverse=True)
            
            result_text = f"""🎯 **Employee Turnover Risk Analysis**

**Analysis Period:** Last {lookback_months} months
**Total Employees Analyzed:** {len(employee_data)}
**High Risk Employees:** {len(risk_employees)}
**Low Risk Employees:** {len(low_risk_employees)}
**Generated:** {current_date.strftime('%Y-%m-%d %H:%M')}

**🚨 HIGH RISK EMPLOYEES (Score ≥ 40):**"""
            
            if risk_employees:
                for emp in risk_employees[:10]:  # Top 10 high-risk employees
                    result_text += f"""

**{emp['name']}** - Risk Score: {emp['risk_score']}/100
• Role: {emp['role']}
• Department: {emp['department']}
• Attendance Rate: {emp['attendance_rate']:.1f}%
• Risk Factors: {', '.join(emp['risk_factors']) if emp['risk_factors'] else 'General risk factors'}"""
            else:
                result_text += "\n✅ No employees identified as high risk!"
            
            result_text += f"""

**📊 RISK DISTRIBUTION:**
• High Risk (40-100): {len([e for e in risk_employees if e['risk_score'] >= 40])} employees
• Moderate Risk (20-39): {len([e for e in employee_data if 20 <= (40 if e in [emp['name'] for emp in risk_employees] else 10) <= 39])} employees  
• Low Risk (0-19): {len(low_risk_employees)} employees

**🎯 RECOMMENDED ACTIONS:**"""
            
            if risk_employees:
                result_text += """
1. **Immediate Actions:**
   • Schedule one-on-one meetings with high-risk employees
   • Investigate specific concerns and challenges
   • Review workload and work-life balance
   
2. **Medium-term Strategies:**
   • Implement mentorship programs
   • Provide career development opportunities
   • Address workplace culture issues
   
3. **Retention Initiatives:**
   • Improve recognition and rewards programs
   • Offer flexible work arrangements
   • Enhance professional development support"""
            else:
                result_text += """
1. **Maintain current positive environment**
2. **Continue regular employee engagement surveys**
3. **Recognize and reward good performance**
4. **Monitor trends for early warning signs**"""
            
            result_text += f"""

**📈 SUCCESS METRICS TO TRACK:**
• Monthly employee satisfaction scores
• Attendance rate improvements  
• Reduced absenteeism patterns
• Employee feedback sentiment
• Exit interview insights

*Note: This predictive analysis is based on available HR data. Consider conducting employee engagement surveys for more comprehensive insights.*"""
            
            return result_text
            
        except Exception as e:
            return f"An error occurred during turnover risk analysis: {e}"

@tool
def generate_compliance_report(report_type: str = "attendance", period: str = "current_month") -> str:
    """
    Generates compliance reports for various HR areas.
    Parameters:
    - report_type: Type of compliance report (attendance, leave, general)
    - period: Report period (current_month, current_quarter, current_year)
    """
    with SessionLocal() as db:
        try:
            current_date = datetime.now()
            
            # Define period dates
            if period == "current_month":
                start_date = current_date.replace(day=1).date()
                end_date = current_date.date()
                period_label = current_date.strftime("%B %Y")
            elif period == "current_quarter":
                quarter = ((current_date.month - 1) // 3) + 1
                start_date = datetime(current_date.year, (quarter-1)*3 + 1, 1).date()
                end_date = current_date.date()
                period_label = f"Q{quarter} {current_date.year}"
            elif period == "current_year":
                start_date = datetime(current_date.year, 1, 1).date()
                end_date = current_date.date()
                period_label = str(current_date.year)
            else:
                start_date = current_date.replace(day=1).date()
                end_date = current_date.date()
                period_label = current_date.strftime("%B %Y")
            
            if report_type == "attendance":
                # Attendance Compliance Report
                compliance_query = text("""
                    SELECT 
                        e.name,
                        d.name as department_name,
                        COUNT(a.id) as total_records,
                        COUNT(CASE WHEN a.status = 'Present' THEN 1 END) as present_count,
                        COUNT(CASE WHEN a.status = 'Absent' THEN 1 END) as absent_count,
                        COUNT(CASE WHEN a.status LIKE '%Leave%' THEN 1 END) as leave_count
                    FROM employees e
                    LEFT JOIN departments d ON e.department_id = d.id
                    LEFT JOIN attendances a ON e.id = a.employee_id 
                        AND a.attendance_date BETWEEN :start_date AND :end_date
                    WHERE e.is_active = true
                    GROUP BY e.id, e.name, d.name
                    HAVING COUNT(a.id) > 0
                    ORDER BY e.name
                """)
                
                result = db.execute(compliance_query, {
                    'start_date': start_date,
                    'end_date': end_date
                })
                compliance_data = result.fetchall()
                
                # Compliance thresholds
                MIN_ATTENDANCE_RATE = 75.0
                MAX_ABSENCE_RATE = 10.0
                
                compliant_employees = []
                non_compliant_employees = []
                
                for emp_data in compliance_data:
                    name, dept_name, total_records, present_count, absent_count, leave_count = emp_data
                    
                    attendance_rate = (present_count / total_records * 100) if total_records > 0 else 0
                    absence_rate = (absent_count / total_records * 100) if total_records > 0 else 0
                    
                    compliance_status = {
                        'name': name,
                        'department': dept_name or 'Not assigned',
                        'attendance_rate': attendance_rate,
                        'absence_rate': absence_rate,
                        'total_days': total_records,
                        'present_days': present_count,
                        'absent_days': absent_count,
                        'leave_days': leave_count
                    }
                    
                    if attendance_rate >= MIN_ATTENDANCE_RATE and absence_rate <= MAX_ABSENCE_RATE:
                        compliant_employees.append(compliance_status)
                    else:
                        non_compliant_employees.append(compliance_status)
                
                return f"""📋 **Attendance Compliance Report**

**Period:** {period_label}
**Report Type:** {report_type.title()}
**Generated:** {current_date.strftime('%Y-%m-%d %H:%M')}

**📊 COMPLIANCE STANDARDS:**
• Minimum Attendance Rate: {MIN_ATTENDANCE_RATE}%
• Maximum Absence Rate: {MAX_ABSENCE_RATE}%

**✅ COMPLIANT EMPLOYEES ({len(compliant_employees)}):**"""
                
                result_text = result_text if 'result_text' in locals() else ""
                
                for emp in compliant_employees[:10]:  # First 10 compliant employees
                    result_text += f"""
• **{emp['name']}** ({emp['department']})
  Attendance: {emp['attendance_rate']:.1f}% | Absence: {emp['absence_rate']:.1f}%"""
                
                if len(compliant_employees) > 10:
                    result_text += f"\n  ... and {len(compliant_employees) - 10} more compliant employees"
                
                result_text += f"""

**⚠️ NON-COMPLIANT EMPLOYEES ({len(non_compliant_employees)}):**"""
                
                for emp in non_compliant_employees:
                    result_text += f"""
• **{emp['name']}** ({emp['department']})
  Attendance: {emp['attendance_rate']:.1f}% | Absence: {emp['absence_rate']:.1f}%
  Issues: {'Low attendance' if emp['attendance_rate'] < MIN_ATTENDANCE_RATE else ''} {'High absence' if emp['absence_rate'] > MAX_ABSENCE_RATE else ''}"""
                
                if not non_compliant_employees:
                    result_text += "\n✅ All employees meet compliance standards!"
                
                # Compliance summary
                total_employees = len(compliant_employees) + len(non_compliant_employees)
                compliance_rate = (len(compliant_employees) / total_employees * 100) if total_employees > 0 else 0
                
                result_text += f"""

**📈 COMPLIANCE SUMMARY:**
• Overall Compliance Rate: {compliance_rate:.1f}%
• Total Employees Reviewed: {total_employees}
• Requiring Action: {len(non_compliant_employees)}

**🎯 RECOMMENDATIONS:**"""
                
                if len(non_compliant_employees) > 0:
                    result_text += """
1. Schedule meetings with non-compliant employees
2. Investigate root causes of attendance issues
3. Implement corrective action plans
4. Provide additional support and resources
5. Monitor progress monthly"""
                else:
                    result_text += """
1. Maintain current attendance management practices
2. Continue regular monitoring and reporting
3. Recognize employees with excellent attendance
4. Share best practices across the organization"""
                
                return result_text
                
            else:
                return f"Compliance report type '{report_type}' is not yet implemented. Available types: attendance"
                
        except Exception as e:
            return f"An error occurred while generating the compliance report: {e}"

@tool
def create_custom_hr_report(report_request: str, include_charts: bool = False) -> str:
    """
    Creates a custom HR report based on natural language request.
    Parameters:
    - report_request: Natural language description of the desired report
    - include_charts: Whether to include chart descriptions (default False)
    """
    with SessionLocal() as db:
        try:
            # Use AI to interpret the report request and generate appropriate queries
            ai_model = ChatOpenAI(model="gpt-4o", temperature=0.1)
            
            # Get database schema for context
            schema_query = """
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name IN ('employees', 'departments', 'attendances', 'leave_requests', 'leave_balances')
                ORDER BY table_name, column_name
            """
            
            schema_result = db.execute(text(schema_query))
            schema_info = schema_result.fetchall()
            
            # Create schema description
            schema_desc = "Available database tables and columns:\n"
            current_table = ""
            for table, column, data_type in schema_info:
                if table != current_table:
                    schema_desc += f"\n{table}: "
                    current_table = table
                schema_desc += f"{column}({data_type}), "
            
            # Generate report using AI
            report_prompt = f"""
            You are an HR analytics expert. Create a comprehensive report based on this request: "{report_request}"
            
            Available database schema:
            {schema_desc}
            
            Current date: {datetime.now().strftime('%Y-%m-%d')}
            
            Provide:
            1. Report title and overview
            2. Key metrics and findings
            3. Data analysis and insights
            4. Trends and patterns
            5. Actionable recommendations
            
            Format as a professional HR report with clear sections and bullet points.
            If specific data is needed but not available, note it as "Data collection needed".
            """
            
            if include_charts:
                report_prompt += "\n\nAlso include descriptions of recommended charts and visualizations."
            
            ai_response = ai_model.invoke(report_prompt).content
            
            # Add metadata to the report
            final_report = f"""📊 **Custom HR Report**

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Request:** {report_request}

{ai_response}

---
**Report Generation Notes:**
• This report was generated using AI analysis of available HR data
• Recommendations are based on current system capabilities
• For specific data points not shown, database enhancements may be needed
• Report accuracy depends on data quality and completeness

**📞 For questions or clarifications about this report, please contact the HR analytics team.**"""
            
            return final_report
            
        except Exception as e:
            return f"An error occurred while creating the custom HR report: {e}"

@tool
def track_hr_kpis(kpi_category: str = "all") -> str:
    """
    Tracks and reports on key HR Key Performance Indicators (KPIs).
    Parameters:
    - kpi_category: Category of KPIs to track (all, workforce, attendance, performance, engagement)
    """
    with SessionLocal() as db:
        try:
            current_date = datetime.now()
            current_month_start = current_date.replace(day=1).date()
            current_year_start = datetime(current_date.year, 1, 1).date()
            
            kpi_results = {}
            
            if kpi_category in ["all", "workforce"]:
                # Workforce KPIs
                total_employees = db.query(models.Employee).filter(models.Employee.is_active == True).count()
                total_departments = db.query(models.Department).count()
                
                kpi_results["workforce"] = {
                    "total_active_employees": total_employees,
                    "total_departments": total_departments,
                    "avg_employees_per_dept": total_employees / total_departments if total_departments > 0 else 0
                }
            
            if kpi_category in ["all", "attendance"]:
                # Attendance KPIs
                attendance_query = text("""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(CASE WHEN status = 'Present' THEN 1 END) as present_count,
                        COUNT(CASE WHEN status LIKE '%Leave%' THEN 1 END) as leave_count,
                        COUNT(CASE WHEN status = 'Absent' THEN 1 END) as absent_count
                    FROM attendances 
                    WHERE attendance_date >= :month_start
                """)
                
                att_result = db.execute(attendance_query, {'month_start': current_month_start}).fetchone()
                
                if att_result:
                    total_records, present_count, leave_count, absent_count = att_result
                    kpi_results["attendance"] = {
                        "attendance_rate": (present_count / total_records * 100) if total_records > 0 else 0,
                        "absence_rate": (absent_count / total_records * 100) if total_records > 0 else 0,
                        "leave_utilization": (leave_count / total_records * 100) if total_records > 0 else 0,
                        "total_attendance_records": total_records
                    }
            
            if kpi_category in ["all", "engagement"]:
                # Engagement KPIs (based on available data)
                leave_request_query = text("""
                    SELECT 
                        COUNT(*) as total_requests,
                        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_requests,
                        AVG(EXTRACT(EPOCH FROM (CURRENT_DATE - leave_date))/86400) as avg_request_lead_time
                    FROM leave_requests 
                    WHERE leave_date >= :year_start
                """)
                
                leave_result = db.execute(leave_request_query, {'year_start': current_year_start}).fetchone()
                
                if leave_result:
                    total_requests, pending_requests, avg_lead_time = leave_result
                    kpi_results["engagement"] = {
                        "leave_request_efficiency": ((total_requests - pending_requests) / total_requests * 100) if total_requests > 0 else 0,
                        "pending_requests_backlog": pending_requests or 0,
                        "avg_leave_request_lead_time": abs(avg_lead_time) if avg_lead_time else 0
                    }
            
            # Format KPI report
            report = f"""📊 **HR Key Performance Indicators (KPIs)**

**Period:** {current_date.strftime('%B %Y')}
**Category:** {kpi_category.title()}
**Generated:** {current_date.strftime('%Y-%m-%d %H:%M')}

"""
            
            if "workforce" in kpi_results:
                wf = kpi_results["workforce"]
                report += f"""**👥 WORKFORCE KPIs:**
• Total Active Employees: {wf['total_active_employees']}
• Total Departments: {wf['total_departments']}
• Average Team Size: {wf['avg_employees_per_dept']:.1f} employees per department

"""
            
            if "attendance" in kpi_results:
                att = kpi_results["attendance"]
                report += f"""**📈 ATTENDANCE KPIs:**
• Attendance Rate: {att['attendance_rate']:.1f}% {'✅' if att['attendance_rate'] >= 85 else '⚠️' if att['attendance_rate'] >= 75 else '❌'}
• Absence Rate: {att['absence_rate']:.1f}% {'✅' if att['absence_rate'] <= 5 else '⚠️' if att['absence_rate'] <= 10 else '❌'}
• Leave Utilization: {att['leave_utilization']:.1f}%
• Total Records: {att['total_attendance_records']}

"""
            
            if "engagement" in kpi_results:
                eng = kpi_results["engagement"]
                report += f"""**🎯 ENGAGEMENT KPIs:**
• Leave Request Efficiency: {eng['leave_request_efficiency']:.1f}% {'✅' if eng['leave_request_efficiency'] >= 90 else '⚠️' if eng['leave_request_efficiency'] >= 75 else '❌'}
• Pending Requests Backlog: {eng['pending_requests_backlog']} {'✅' if eng['pending_requests_backlog'] <= 5 else '❌'}
• Avg. Request Lead Time: {eng['avg_leave_request_lead_time']:.1f} days

"""
            
            report += """**📊 KPI PERFORMANCE INDICATORS:**
✅ = Target Met | ⚠️ = Needs Attention | ❌ = Below Target

**🎯 RECOMMENDED TARGETS:**
• Attendance Rate: ≥85%
• Absence Rate: ≤5%
• Leave Request Efficiency: ≥90%
• Pending Requests: ≤5

**📈 IMPROVEMENT ACTIONS:**
• Review any KPIs marked with ⚠️ or ❌
• Implement targeted improvement plans
• Monitor progress monthly
• Celebrate achievements for ✅ metrics"""
            
            return report
            
        except Exception as e:
            return f"An error occurred while tracking HR KPIs: {e}"

# Export all analytics tools
analytics_tools = [
    generate_hr_dashboard_metrics,
    analyze_attendance_patterns,
    predict_employee_turnover_risk,
    generate_compliance_report,
    create_custom_hr_report,
    track_hr_kpis
]