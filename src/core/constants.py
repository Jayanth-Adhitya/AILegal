"""Constants and enumerations for the Legal AI system."""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class PolicyType:
    """Policy type definition with metadata."""
    id: str
    name: str
    description: str
    category: str


# Policy Type Taxonomy - 20 common policy types organized by category
POLICY_TYPES: List[PolicyType] = [
    # Corporate Governance
    PolicyType(
        id="non_disclosure_agreement",
        name="Non-Disclosure Agreement (NDA)",
        description="Protect confidential business information shared between parties",
        category="Corporate Governance"
    ),
    PolicyType(
        id="service_level_agreement",
        name="Service Level Agreement (SLA)",
        description="Define service standards, responsibilities, and guarantees",
        category="Corporate Governance"
    ),
    PolicyType(
        id="data_privacy_policy",
        name="Data Privacy Policy",
        description="Govern collection, use, and protection of personal data",
        category="Corporate Governance"
    ),
    PolicyType(
        id="information_security_policy",
        name="Information Security Policy",
        description="Establish security controls and practices for data protection",
        category="Corporate Governance"
    ),

    # HR & Employment
    PolicyType(
        id="employee_code_of_conduct",
        name="Employee Code of Conduct",
        description="Define expected behaviors and ethical standards for employees",
        category="HR & Employment"
    ),
    PolicyType(
        id="remote_work_policy",
        name="Remote Work Policy",
        description="Set guidelines for remote and hybrid work arrangements",
        category="HR & Employment"
    ),
    PolicyType(
        id="leave_attendance_policy",
        name="Leave and Attendance Policy",
        description="Outline leave entitlements, attendance requirements, and procedures",
        category="HR & Employment"
    ),
    PolicyType(
        id="workplace_safety_policy",
        name="Workplace Safety Policy",
        description="Ensure employee health and safety in the workplace",
        category="HR & Employment"
    ),

    # Compliance
    PolicyType(
        id="anti_corruption_policy",
        name="Anti-Corruption and Bribery Policy",
        description="Prevent corruption, bribery, and unethical business practices",
        category="Compliance"
    ),
    PolicyType(
        id="whistleblower_policy",
        name="Whistleblower Policy",
        description="Protect employees who report misconduct or violations",
        category="Compliance"
    ),
    PolicyType(
        id="conflict_of_interest_policy",
        name="Conflict of Interest Policy",
        description="Identify and manage conflicts between personal and company interests",
        category="Compliance"
    ),
    PolicyType(
        id="records_retention_policy",
        name="Records Retention Policy",
        description="Define how long to retain different types of business records",
        category="Compliance"
    ),

    # Operations
    PolicyType(
        id="procurement_policy",
        name="Procurement Policy",
        description="Govern purchasing processes and supplier relationships",
        category="Operations"
    ),
    PolicyType(
        id="vendor_management_policy",
        name="Vendor Management Policy",
        description="Manage third-party vendor relationships and performance",
        category="Operations"
    ),
    PolicyType(
        id="quality_assurance_policy",
        name="Quality Assurance Policy",
        description="Ensure consistent product and service quality standards",
        category="Operations"
    ),
    PolicyType(
        id="business_continuity_policy",
        name="Business Continuity Policy",
        description="Prepare for and respond to business disruptions",
        category="Operations"
    ),

    # Technology
    PolicyType(
        id="acceptable_use_policy",
        name="Acceptable Use Policy (IT)",
        description="Define proper use of company IT resources and systems",
        category="Technology"
    ),
    PolicyType(
        id="byod_policy",
        name="Bring Your Own Device (BYOD) Policy",
        description="Govern personal device use for work purposes",
        category="Technology"
    ),
    PolicyType(
        id="social_media_policy",
        name="Social Media Policy",
        description="Guide employee use of social media for business and personal use",
        category="Technology"
    ),
    PolicyType(
        id="email_communication_policy",
        name="Email and Communication Policy",
        description="Set standards for professional business communications",
        category="Technology"
    ),
]


# Category grouping for UI display
POLICY_CATEGORIES = [
    "Corporate Governance",
    "HR & Employment",
    "Compliance",
    "Operations",
    "Technology"
]


def get_policy_type_by_id(policy_type_id: str) -> PolicyType | None:
    """Get policy type definition by ID."""
    for policy_type in POLICY_TYPES:
        if policy_type.id == policy_type_id:
            return policy_type
    return None


def get_policy_types_by_category(category: str) -> List[PolicyType]:
    """Get all policy types in a specific category."""
    return [pt for pt in POLICY_TYPES if pt.category == category]


def validate_policy_type(policy_type_id: str) -> bool:
    """Validate that a policy type ID exists."""
    return any(pt.id == policy_type_id for pt in POLICY_TYPES)


def get_policy_types_dict() -> Dict[str, List[Dict[str, str]]]:
    """Get policy types grouped by category as dictionary for API responses."""
    result = {}
    for category in POLICY_CATEGORIES:
        result[category] = [
            {
                "id": pt.id,
                "name": pt.name,
                "description": pt.description
            }
            for pt in POLICY_TYPES if pt.category == category
        ]
    return result
