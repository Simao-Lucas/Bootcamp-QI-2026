from typing import List

from models import Employee


class EmployeeDTO:
    @staticmethod
    def obj_to_dict(employee: Employee) -> dict:
        terminated_at = None
        if employee.terminated_at is not None:
            terminated_at = employee.terminated_at.isoformat()

        dto = dict()
        dto["employee_key"] = employee.employee_key
        dto["company_key"] = employee.company.company_key
        dto["position_key"] = employee.position.position_key
        dto["name"] = employee.name
        dto["document_number"] = employee.document_number
        dto["email"] = employee.email
        dto["hired_at"] = employee.hired_at.isoformat()
        dto["terminated_at"] = terminated_at

        return dto

    @staticmethod
    def list_obj_to_list_dict(employees_list: List[Employee]) -> List[dict]:
        employees_dict_list = []

        for employee in employees_list:
            employees_dict_list.append(EmployeeDTO.obj_to_dict(employee))

        return employees_dict_list

    @staticmethod
    def only_obj_key(employee: Employee) -> dict:
        dto = dict()
        dto["employee_key"] = employee.employee_key

        return dto
