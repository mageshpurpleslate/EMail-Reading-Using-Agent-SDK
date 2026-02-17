from dataclasses import dataclass, field


@dataclass
class AttendanceException:
    employee_name: str = ""
    employee_id: str = ""
    exception_type: str = ""  # late-in, early-out, half-day, work-from-home, leave
    date: str = ""
    reason: str = ""
    duration: str = ""  # e.g., "2 hours late", "arriving at 11:00 AM"
    raw_text: str = ""

    def to_summary(self) -> str:
        lines = ["**Attendance Exception Request**", ""]
        lines.append(f"- **Type:** {self.exception_type or 'Unknown'}")
        if self.employee_name:
            lines.append(f"- **Employee:** {self.employee_name}")
        if self.employee_id:
            lines.append(f"- **Employee ID:** {self.employee_id}")
        lines.append(f"- **Date:** {self.date or 'Not specified'}")
        if self.duration:
            lines.append(f"- **Duration:** {self.duration}")
        lines.append(f"- **Reason:** {self.reason or 'Not provided'}")
        lines.append("")
        lines.append("---")
        lines.append("*Please confirm: Approve or Reject this request.*")
        return "\n".join(lines)
