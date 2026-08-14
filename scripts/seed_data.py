import sys
import os
import argparse
import logging
import json
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from neo4j import GraphDatabase, Driver

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_data")

# Seed data definitions
EMPLOYEES = [
    {"id": "emp-001", "name": "Alex Rivera", "email": "alex.rivera@wexa.ai", "department": "Security", "status": "offboarded", "offboarded_at": "2026-03-15T10:00:00Z"},
    {"id": "emp-002", "name": "Sarah Chen", "email": "sarah.chen@wexa.ai", "department": "DevOps", "status": "offboarded", "offboarded_at": "2026-04-01T14:30:00Z"},
    {"id": "emp-003", "name": "David Kim", "email": "david.kim@wexa.ai", "department": "Engineering", "status": "offboarded", "offboarded_at": "2026-05-10T09:15:00Z"},
    {"id": "emp-004", "name": "Elena Rostova", "email": "elena.rostova@wexa.ai", "department": "Finance", "status": "offboarded", "offboarded_at": "2026-06-20T16:45:00Z"},
    {"id": "emp-005", "name": "Marcus Vance", "email": "marcus.vance@wexa.ai", "department": "Product", "status": "offboarded", "offboarded_at": "2026-07-05T11:20:00Z"},
    {"id": "emp-006", "name": "Rachel Adams", "email": "rachel.adams@wexa.ai", "department": "Security", "status": "offboarded", "offboarded_at": "2026-07-18T08:00:00Z"},
    {"id": "emp-007", "name": "Vikram Patel", "email": "vikram.patel@wexa.ai", "department": "DevOps", "status": "offboarded", "offboarded_at": "2026-08-01T13:10:00Z"},
    {"id": "emp-008", "name": "Jessica Taylor", "email": "jessica.taylor@wexa.ai", "department": "HR", "status": "offboarded", "offboarded_at": "2026-01-15T09:00:00Z"},

    # Active Employees
    {"id": "emp-010", "name": "Jordan Lee", "email": "jordan.lee@wexa.ai", "department": "Engineering", "status": "active", "offboarded_at": None},
    {"id": "emp-011", "name": "Morgan Smith", "email": "morgan.smith@wexa.ai", "department": "DevOps", "status": "active", "offboarded_at": None},
    {"id": "emp-012", "name": "Taylor Wong", "email": "taylor.wong@wexa.ai", "department": "Security", "status": "active", "offboarded_at": None},
    {"id": "emp-013", "name": "Chris Martinez", "email": "chris.martinez@wexa.ai", "department": "Product", "status": "active", "offboarded_at": None},
    {"id": "emp-014", "name": "Sam Gupta", "email": "sam.gupta@wexa.ai", "department": "Engineering", "status": "active", "offboarded_at": None},
    {"id": "emp-015", "name": "Pat Johnson", "email": "pat.johnson@wexa.ai", "department": "Finance", "status": "active", "offboarded_at": None},
    {"id": "emp-016", "name": "Casey Wright", "email": "casey.wright@wexa.ai", "department": "HR", "status": "active", "offboarded_at": None},
]

SLACK_GROUPS = [
    {"id": "sg-01", "name": "secops-lead"},
    {"id": "sg-02", "name": "platform-infra"},
    {"id": "sg-03", "name": "data-eng"},
    {"id": "sg-04", "name": "billing-admins"},
    {"id": "sg-05", "name": "incident-response"},
    {"id": "sg-06", "name": "eng-all"},
    {"id": "sg-07", "name": "devops-core"},
]

OKTA_GROUPS = [
    {"id": "og-01", "name": "okta-secops-lead"},
    {"id": "og-02", "name": "okta-devops-core"},
    {"id": "og-03", "name": "okta-data-eng"},
    {"id": "og-04", "name": "okta-billing-admins"},
    {"id": "og-05", "name": "okta-shadow-devs"},
    {"id": "og-06", "name": "okta-eng-all"},
]

AWS_ROLES = [
    {"id": "ar-01", "name": "ProductionAdmin", "arn": "arn:aws:iam::123456789012:role/ProductionAdmin"},
    {"id": "ar-02", "name": "EC2ClusterAdmin", "arn": "arn:aws:iam::123456789012:role/EC2ClusterAdmin"},
    {"id": "ar-03", "name": "S3DataVaultAccess", "arn": "arn:aws:iam::123456789012:role/S3DataVaultAccess"},
    {"id": "ar-04", "name": "BillingVaultAccess", "arn": "arn:aws:iam::123456789012:role/BillingVaultAccess"},
    {"id": "ar-05", "name": "CustomerDataReadWrite", "arn": "arn:aws:iam::123456789012:role/CustomerDataReadWrite"},
]

CLOUD_RESOURCES = [
    {"id": "cr-01", "name": "prod-auth-secrets-kms", "type": "kms_key", "environment": "production", "sensitivity": "critical"},
    {"id": "cr-02", "name": "prod-kubernetes-control-plane", "type": "ec2_instance", "environment": "production", "sensitivity": "high"},
    {"id": "cr-03", "name": "prod-user-pii-bucket", "type": "s3_bucket", "environment": "production", "sensitivity": "critical"},
    {"id": "cr-04", "name": "prod-financial-transactions-db", "type": "rds_instance", "environment": "production", "sensitivity": "critical"},
    {"id": "cr-05", "name": "prod-billing-db", "type": "rds_instance", "environment": "production", "sensitivity": "high"},
    {"id": "cr-06", "name": "prod-audit-logs-bucket", "type": "s3_bucket", "environment": "production", "sensitivity": "high"},
    {"id": "cr-07", "name": "staging-test-bucket", "type": "s3_bucket", "environment": "staging", "sensitivity": "medium"},
    {"id": "cr-08", "name": "dev-sandbox-ec2", "type": "ec2_instance", "environment": "dev", "sensitivity": "low"},
]

EMP_SLACK_RELSHIPS = [
    {"emp_id": "emp-001", "slack_id": "sg-01", "since": "2024-01-10", "active": True},
    {"emp_id": "emp-002", "slack_id": "sg-02", "since": "2024-02-15", "active": True},
    {"emp_id": "emp-003", "slack_id": "sg-03", "since": "2024-03-01", "active": True},
    {"emp_id": "emp-004", "slack_id": "sg-04", "since": "2024-04-12", "active": True},
    {"emp_id": "emp-006", "slack_id": "sg-05", "since": "2024-05-20", "active": True},
    {"emp_id": "emp-010", "slack_id": "sg-06", "since": "2025-01-05", "active": True},
    {"emp_id": "emp-011", "slack_id": "sg-07", "since": "2025-02-10", "active": True},
]

SLACK_OKTA_RELSHIPS = [
    {"slack_id": "sg-01", "okta_id": "og-01", "synced_at": "2026-01-01T00:00:00Z"},
    {"slack_id": "sg-02", "okta_id": "og-02", "synced_at": "2026-01-01T00:00:00Z"},
    {"slack_id": "sg-03", "okta_id": "og-03", "synced_at": "2026-01-01T00:00:00Z"},
    {"slack_id": "sg-04", "okta_id": "og-04", "synced_at": "2026-01-01T00:00:00Z"},
    {"slack_id": "sg-05", "okta_id": "og-01", "synced_at": "2026-01-01T00:00:00Z"},
]

EMP_OKTA_RELSHIPS = [
    {"emp_id": "emp-005", "okta_id": "og-05", "since": "2024-06-01", "active": True},
]

OKTA_ROLE_RELSHIPS = [
    {"okta_id": "og-01", "role_id": "ar-01", "granted_at": "2024-01-01T00:00:00Z"},
    {"okta_id": "og-02", "role_id": "ar-02", "granted_at": "2024-01-01T00:00:00Z"},
    {"okta_id": "og-03", "role_id": "ar-03", "granted_at": "2024-01-01T00:00:00Z"},
    {"okta_id": "og-04", "role_id": "ar-04", "granted_at": "2024-01-01T00:00:00Z"},
    {"okta_id": "og-05", "role_id": "ar-05", "granted_at": "2024-01-01T00:00:00Z"},
]

ROLE_RESOURCE_RELSHIPS = [
    {"role_id": "ar-01", "resource_id": "cr-01", "access_level": "admin", "granted_at": "2024-01-01T00:00:00Z"},
    {"role_id": "ar-01", "resource_id": "cr-05", "access_level": "write", "granted_at": "2024-01-01T00:00:00Z"},
    {"role_id": "ar-02", "resource_id": "cr-02", "access_level": "admin", "granted_at": "2024-01-01T00:00:00Z"},
    {"role_id": "ar-03", "resource_id": "cr-03", "access_level": "admin", "granted_at": "2024-01-01T00:00:00Z"},
    {"role_id": "ar-04", "resource_id": "cr-04", "access_level": "write", "granted_at": "2024-01-01T00:00:00Z"},
    {"role_id": "ar-05", "resource_id": "cr-03", "access_level": "read", "granted_at": "2024-01-01T00:00:00Z"},
]

EMP_DIRECT_RESOURCE_RELSHIPS = [
    {"emp_id": "emp-007", "resource_id": "cr-02", "access_level": "admin", "granted_at": "2024-01-10T00:00:00Z", "revoked_at": None},
]

def save_local_fallback():
    os.makedirs("static/data", exist_ok=True)
    fallback_data = {
        "employees": EMPLOYEES,
        "slack_groups": SLACK_GROUPS,
        "okta_groups": OKTA_GROUPS,
        "aws_roles": AWS_ROLES,
        "cloud_resources": CLOUD_RESOURCES,
        "emp_slack": EMP_SLACK_RELSHIPS,
        "slack_okta": SLACK_OKTA_RELSHIPS,
        "emp_okta": EMP_OKTA_RELSHIPS,
        "okta_role": OKTA_ROLE_RELSHIPS,
        "role_resource": ROLE_RESOURCE_RELSHIPS,
        "emp_direct": EMP_DIRECT_RESOURCE_RELSHIPS
    }
    filepath = "static/data/mock_graph.json"
    with open(filepath, "w") as f:
        json.dump(fallback_data, f, indent=2)
    logger.info(f"Saved local fallback dataset to {filepath}")

def seed_database(driver: Driver, reset: bool = False):
    with driver.session() as session:
        if reset:
            logger.warning("Reset flag provided. Wiping entire database!")
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Database wiped successfully.")

        session.run("UNWIND $employees AS emp MERGE (e:Employee {id: emp.id}) SET e.name = emp.name, e.email = emp.email, e.department = emp.department, e.status = emp.status, e.offboarded_at = emp.offboarded_at", employees=EMPLOYEES)
        session.run("UNWIND $groups AS g MERGE (sg:SlackGroup {id: g.id}) SET sg.name = g.name", groups=SLACK_GROUPS)
        session.run("UNWIND $groups AS g MERGE (og:OktaGroup {id: g.id}) SET og.name = g.name", groups=OKTA_GROUPS)
        session.run("UNWIND $roles AS r MERGE (ar:AWSRole {id: r.id}) SET ar.name = r.name, ar.arn = r.arn", roles=AWS_ROLES)
        session.run("UNWIND $resources AS res MERGE (cr:CloudResource {id: res.id}) SET cr.name = res.name, cr.type = res.type, cr.environment = res.environment, cr.sensitivity = res.sensitivity", resources=CLOUD_RESOURCES)

        session.run("UNWIND $relships AS rel MATCH (e:Employee {id: rel.emp_id}) MATCH (sg:SlackGroup {id: rel.slack_id}) MERGE (e)-[r:MEMBER_OF]->(sg) SET r.since = rel.since, r.active = rel.active", relships=EMP_SLACK_RELSHIPS)
        session.run("UNWIND $relships AS rel MATCH (sg:SlackGroup {id: rel.slack_id}) MATCH (og:OktaGroup {id: rel.okta_id}) MERGE (sg)-[r:MIRRORS]->(og) SET r.synced_at = rel.synced_at", relships=SLACK_OKTA_RELSHIPS)
        session.run("UNWIND $relships AS rel MATCH (e:Employee {id: rel.emp_id}) MATCH (og:OktaGroup {id: rel.okta_id}) MERGE (e)-[r:MEMBER_OF]->(og) SET r.since = rel.since, r.active = rel.active", relships=EMP_OKTA_RELSHIPS)
        session.run("UNWIND $relships AS rel MATCH (og:OktaGroup {id: rel.okta_id}) MATCH (ar:AWSRole {id: rel.role_id}) MERGE (og)-[r:GRANTS_ROLE]->(ar) SET r.granted_at = rel.granted_at", relships=OKTA_ROLE_RELSHIPS)
        session.run("UNWIND $relships AS rel MATCH (ar:AWSRole {id: rel.role_id}) MATCH (cr:CloudResource {id: rel.resource_id}) MERGE (ar)-[r:CAN_ACCESS]->(cr) SET r.access_level = rel.access_level, r.granted_at = rel.granted_at", relships=ROLE_RESOURCE_RELSHIPS)
        session.run("UNWIND $relships AS rel MATCH (e:Employee {id: rel.emp_id}) MATCH (cr:CloudResource {id: rel.resource_id}) MERGE (e)-[r:DIRECTLY_ACCESSES]->(cr) SET r.access_level = rel.access_level, r.granted_at = rel.granted_at, r.revoked_at = rel.revoked_at", relships=EMP_DIRECT_RESOURCE_RELSHIPS)

        logger.info("Successfully seeded live CognoDB instance!")

def main():
    parser = argparse.ArgumentParser(description="Seed CognoDB for OffboardGuard.")
    parser.add_argument("--reset", action="store_true", help="Wipe database before seeding.")
    args = parser.parse_args()

    # Always generate/update local fallback dataset so offline demo mode works 100%
    save_local_fallback()

    logger.info(f"Attempting connection to CognoDB at {settings.COGNO_URI}...")
    try:
        driver = GraphDatabase.driver(
            settings.COGNO_URI,
            auth=(settings.COGNO_USER, settings.COGNO_PASSWORD)
        )
        driver.verify_connectivity()
        logger.info("Connected to live CognoDB instance.")
        seed_database(driver, reset=args.reset)
        driver.close()
        logger.info("Seeding to CognoDB completed successfully!")
    except Exception as e:
        logger.warning(f"CognoDB cloud connection failed ({e}).")
        logger.info("Local fallback seed data is ready at static/data/mock_graph.json for Offline Demo Mode!")

if __name__ == "__main__":
    main()
