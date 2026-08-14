import os
import json
from typing import Dict, List, Any

# Local fallback data loader using absolute path
def load_fallback_data() -> Dict[str, Any]:
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    filepath = os.path.join(base_dir, "static", "data", "mock_graph.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# 1. Flagship Ghost Access Detector (Multi-hop path query)
def query_ghost_access_chains(tx, limit: int = 50, environment: str = "production") -> List[Dict[str, Any]]:
    if tx is None:
        data = load_fallback_data()
        emp_map = {e["id"]: e for e in data.get("employees", [])}
        slack_map = {s["id"]: s for s in data.get("slack_groups", [])}
        okta_map = {o["id"]: o for o in data.get("okta_groups", [])}
        role_map = {r["id"]: r for r in data.get("aws_roles", [])}
        resource_map = {r["id"]: r for r in data.get("cloud_resources", [])}

        chains = []
        for es in data.get("emp_slack", []):
            emp = emp_map.get(es["emp_id"])
            if not emp or emp["status"] != "offboarded": continue
            slack = slack_map.get(es["slack_id"])
            if not slack: continue

            for so in data.get("slack_okta", []):
                if so["slack_id"] != slack["id"]: continue
                okta = okta_map.get(so["okta_id"])
                if not okta: continue

                for or_rel in data.get("okta_role", []):
                    if or_rel["okta_id"] != okta["id"]: continue
                    role = role_map.get(or_rel["role_id"])
                    if not role: continue

                    for rr in data.get("role_resource", []):
                        if rr["role_id"] != role["id"]: continue
                        res = resource_map.get(rr["resource_id"])
                        if not res or res.get("environment") != environment: continue

                        chains.append({
                            "employee_id": emp["id"],
                            "employee_name": emp["name"],
                            "employee_email": emp["email"],
                            "department": emp["department"],
                            "offboarded_at": emp.get("offboarded_at"),
                            "resource_id": res["id"],
                            "resource_name": res["name"],
                            "resource_type": res["type"],
                            "environment": res["environment"],
                            "sensitivity": res["sensitivity"],
                            "hops": 4,
                            "path_nodes": [
                                {"id": emp["id"], "name": emp["name"], "label": "Employee"},
                                {"id": slack["id"], "name": slack["name"], "label": "SlackGroup"},
                                {"id": okta["id"], "name": okta["name"], "label": "OktaGroup"},
                                {"id": role["id"], "name": role["name"], "label": "AWSRole"},
                                {"id": res["id"], "name": res["name"], "label": "CloudResource"}
                            ],
                            "path_relationships": [{"type": "MEMBER_OF"}, {"type": "MIRRORS"}, {"type": "GRANTS_ROLE"}, {"type": "CAN_ACCESS"}]
                        })

        for eo in data.get("emp_okta", []):
            emp = emp_map.get(eo["emp_id"])
            if not emp or emp["status"] != "offboarded": continue
            okta = okta_map.get(eo["okta_id"])
            if not okta: continue

            for or_rel in data.get("okta_role", []):
                if or_rel["okta_id"] != okta["id"]: continue
                role = role_map.get(or_rel["role_id"])
                if not role: continue

                for rr in data.get("role_resource", []):
                    if rr["role_id"] != role["id"]: continue
                    res = resource_map.get(rr["resource_id"])
                    if not res or res.get("environment") != environment: continue

                    chains.append({
                        "employee_id": emp["id"],
                        "employee_name": emp["name"],
                        "employee_email": emp["email"],
                        "department": emp["department"],
                        "offboarded_at": emp.get("offboarded_at"),
                        "resource_id": res["id"],
                        "resource_name": res["name"],
                        "resource_type": res["type"],
                        "environment": res["environment"],
                        "sensitivity": res["sensitivity"],
                        "hops": 3,
                        "path_nodes": [
                            {"id": emp["id"], "name": emp["name"], "label": "Employee"},
                            {"id": okta["id"], "name": okta["name"], "label": "OktaGroup"},
                            {"id": role["id"], "name": role["name"], "label": "AWSRole"},
                            {"id": res["id"], "name": res["name"], "label": "CloudResource"}
                        ],
                        "path_relationships": [{"type": "MEMBER_OF"}, {"type": "GRANTS_ROLE"}, {"type": "CAN_ACCESS"}]
                    })

        for ed in data.get("emp_direct", []):
            emp = emp_map.get(ed["emp_id"])
            if not emp or emp["status"] != "offboarded": continue
            res = resource_map.get(ed["resource_id"])
            if not res or res.get("environment") != environment: continue

            chains.append({
                "employee_id": emp["id"],
                "employee_name": emp["name"],
                "employee_email": emp["email"],
                "department": emp["department"],
                "offboarded_at": emp.get("offboarded_at"),
                "resource_id": res["id"],
                "resource_name": res["name"],
                "resource_type": res["type"],
                "environment": res["environment"],
                "sensitivity": res["sensitivity"],
                "hops": 1,
                "path_nodes": [
                    {"id": emp["id"], "name": emp["name"], "label": "Employee"},
                    {"id": res["id"], "name": res["name"], "label": "CloudResource"}
                ],
                "path_relationships": [{"type": "DIRECTLY_ACCESSES"}]
            })

        return chains[:limit]

    cypher = """
    MATCH (e:Employee {status: 'offboarded'})
    MATCH path = (e)-[:MEMBER_OF|MIRRORS|GRANTS_ROLE|CAN_ACCESS|DIRECTLY_ACCESSES*1..6]->(r:CloudResource)
    WHERE r.environment = $environment
    WITH e, r, path, length(path) AS hops
    RETURN e.id AS employee_id,
           e.name AS employee_name,
           e.email AS employee_email,
           e.department AS department,
           e.offboarded_at AS offboarded_at,
           r.id AS resource_id,
           r.name AS resource_name,
           r.type AS resource_type,
           r.environment AS environment,
           r.sensitivity AS sensitivity,
           hops,
           [n IN nodes(path) | {id: n.id, name: n.name, label: labels(n)[0]}] AS path_nodes,
           [rel IN relationships(path) | {type: type(rel)}] AS path_relationships
    ORDER BY CASE r.sensitivity
               WHEN 'critical' THEN 1
               WHEN 'high' THEN 2
               WHEN 'medium' THEN 3
               ELSE 4
             END ASC, hops ASC
    LIMIT $limit
    """
    result = tx.run(cypher, environment=environment, limit=limit)
    return [dict(record) for record in result]


# 2. Single Employee Blast Radius (Guaranteed String IDs & Single Record Output)
def query_employee_blast_radius(tx, employee_id: str) -> Dict[str, Any]:
    if tx is None:
        data = load_fallback_data()
        emp_map = {e["id"]: e for e in data.get("employees", [])}
        emp = emp_map.get(employee_id)
        if not emp: return {}

        nodes = [{"id": emp["id"], "name": emp["name"], "type": "Employee", "department": emp["department"], "status": emp["status"]}]
        edges = []

        slack_ids = [rel["slack_id"] for rel in data.get("emp_slack", []) if rel["emp_id"] == employee_id]
        slack_map = {s["id"]: s for s in data.get("slack_groups", []) if s["id"] in slack_ids}
        for s in slack_map.values():
            nodes.append({"id": s["id"], "name": s["name"], "type": "SlackGroup"})
            edges.append({"id": f"e-{emp['id']}-MEMBER_OF-{s['id']}", "from": emp["id"], "to": s["id"], "label": "MEMBER_OF"})

        okta_ids = [rel["okta_id"] for rel in data.get("slack_okta", []) if rel["slack_id"] in slack_map]
        okta_ids += [rel["okta_id"] for rel in data.get("emp_okta", []) if rel["emp_id"] == employee_id]
        okta_map = {o["id"]: o for o in data.get("okta_groups", []) if o["id"] in okta_ids}
        for o in okta_map.values():
            nodes.append({"id": o["id"], "name": o["name"], "type": "OktaGroup"})
            for s_id in slack_map:
                if any(rel["slack_id"] == s_id and rel["okta_id"] == o["id"] for rel in data.get("slack_okta", [])):
                    edges.append({"id": f"e-{s_id}-MIRRORS-{o['id']}", "from": s_id, "to": o["id"], "label": "MIRRORS"})
            if any(rel["emp_id"] == emp["id"] and rel["okta_id"] == o["id"] for rel in data.get("emp_okta", [])):
                edges.append({"id": f"e-{emp['id']}-MEMBER_OF-{o['id']}", "from": emp["id"], "to": o["id"], "label": "MEMBER_OF"})

        role_ids = [rel["role_id"] for rel in data.get("okta_role", []) if rel["okta_id"] in okta_map]
        role_map = {r["id"]: r for r in data.get("aws_roles", []) if r["id"] in role_ids}
        for r in role_map.values():
            nodes.append({"id": r["id"], "name": r["name"], "type": "AWSRole"})
            for o_id in okta_map:
                if any(rel["okta_id"] == o_id and rel["role_id"] == r["id"] for rel in data.get("okta_role", [])):
                    edges.append({"id": f"e-{o_id}-GRANTS_ROLE-{r['id']}", "from": o_id, "to": r["id"], "label": "GRANTS_ROLE"})

        res_ids = [rel["resource_id"] for rel in data.get("role_resource", []) if rel["role_id"] in role_map]
        res_ids += [rel["resource_id"] for rel in data.get("emp_direct", []) if rel["emp_id"] == employee_id]
        res_map = {cr["id"]: cr for cr in data.get("cloud_resources", []) if cr["id"] in res_ids}
        for cr in res_map.values():
            nodes.append({"id": cr["id"], "name": cr["name"], "type": "CloudResource", "sensitivity": cr["sensitivity"], "environment": cr["environment"]})
            for r_id in role_map:
                if any(rel["role_id"] == r_id and rel["resource_id"] == cr["id"] for rel in data.get("role_resource", [])):
                    edges.append({"id": f"e-{r_id}-CAN_ACCESS-{cr['id']}", "from": r_id, "to": cr["id"], "label": "CAN_ACCESS"})
            if any(rel["emp_id"] == emp["id"] and rel["resource_id"] == cr["id"] for rel in data.get("emp_direct", [])):
                edges.append({"id": f"e-{emp['id']}-DIRECTLY_ACCESSES-{cr['id']}", "from": emp["id"], "to": cr["id"], "label": "DIRECTLY_ACCESSES"})

        return {"employee": emp, "nodes": nodes, "edges": edges}

    cypher = """
    MATCH (e:Employee {id: $employee_id})
    OPTIONAL MATCH path = (e)-[:MEMBER_OF|MIRRORS|GRANTS_ROLE|CAN_ACCESS|DIRECTLY_ACCESSES*1..6]->(n)
    WITH e, collect(DISTINCT path) AS paths
    WITH e,
         reduce(nodes = [e], p IN paths | nodes + CASE WHEN p IS NULL THEN [] ELSE nodes(p) END) AS raw_nodes,
         reduce(rels = [], p IN paths | rels + CASE WHEN p IS NULL THEN [] ELSE relationships(p) END) AS raw_rels
    UNWIND raw_nodes AS n_item
    WITH e, collect(DISTINCT n_item) AS clean_nodes, raw_rels
    UNWIND (CASE WHEN size(raw_rels) = 0 THEN [null] ELSE raw_rels END) AS r_item
    WITH e, clean_nodes, collect(DISTINCT r_item) AS clean_rels
    RETURN {
        id: e.id,
        name: e.name,
        email: e.email,
        department: e.department,
        status: e.status,
        offboarded_at: e.offboarded_at
    } AS employee,
    [n IN clean_nodes WHERE n IS NOT NULL | {
        id: n.id,
        name: coalesce(n.name, n.id),
        type: labels(n)[0],
        sensitivity: n.sensitivity,
        environment: n.environment,
        department: n.department,
        status: n.status
    }] AS nodes,
    [r IN clean_rels WHERE r IS NOT NULL | {
        id: startNode(r).id + "-" + type(r) + "-" + endNode(r).id,
        from: startNode(r).id,
        to: endNode(r).id,
        label: type(r)
    }] AS edges
    """
    result = tx.run(cypher, employee_id=employee_id)
    records = list(result)
    if not records:
        return {}
    rec = records[0]
    return {
        "employee": dict(rec["employee"]),
        "nodes": rec["nodes"],
        "edges": rec["edges"]
    }


# 4. Aggregate Dashboard Stats
def query_dashboard_stats(tx) -> Dict[str, Any]:
    if tx is None:
        data = load_fallback_data()
        employees = data.get("employees", [])
        total = len(employees)
        active = sum(1 for e in employees if e.get("status") == "active")
        offboarded = sum(1 for e in employees if e.get("status") == "offboarded")
        ghost_chains = query_ghost_access_chains(None, limit=100)
        ghost_resources = len(set(g["resource_id"] for g in ghost_chains))

        return {
            "total_employees": total,
            "active_employees": active,
            "offboarded_employees": offboarded,
            "ghost_chains_count": len(ghost_chains),
            "ghost_resources_count": ghost_resources,
            "top_risky_resources": [
                {"resource_id": "cr-01", "resource_name": "prod-auth-secrets-kms", "sensitivity": "critical", "environment": "production", "offboarded_reach_count": 2},
                {"resource_id": "cr-03", "resource_name": "prod-user-pii-bucket", "sensitivity": "critical", "environment": "production", "offboarded_reach_count": 2},
                {"resource_id": "cr-02", "resource_name": "prod-kubernetes-control-plane", "sensitivity": "high", "environment": "production", "offboarded_reach_count": 2},
                {"resource_id": "cr-04", "resource_name": "prod-financial-transactions-db", "sensitivity": "critical", "environment": "production", "offboarded_reach_count": 1},
            ]
        }

    emp_cypher = """
    MATCH (e:Employee)
    RETURN count(e) AS total,
           sum(CASE WHEN e.status = 'active' THEN 1 ELSE 0 END) AS active,
           sum(CASE WHEN e.status = 'offboarded' THEN 1 ELSE 0 END) AS offboarded
    """
    emp_stats = tx.run(emp_cypher).single() or {"total": 0, "active": 0, "offboarded": 0}

    ghost_cypher = """
    MATCH (e:Employee {status: 'offboarded'})
    MATCH path = (e)-[:MEMBER_OF|MIRRORS|GRANTS_ROLE|CAN_ACCESS|DIRECTLY_ACCESSES*1..6]->(r:CloudResource)
    WHERE r.environment = 'production'
    RETURN count(DISTINCT path) AS ghost_chains_count,
           count(DISTINCT r) AS ghost_resources_count
    """
    ghost_stats = tx.run(ghost_cypher).single() or {"ghost_chains_count": 0, "ghost_resources_count": 0}

    risky_cypher = """
    MATCH (e:Employee {status: 'offboarded'})
    MATCH (e)-[:MEMBER_OF|MIRRORS|GRANTS_ROLE|CAN_ACCESS|DIRECTLY_ACCESSES*1..6]->(r:CloudResource)
    RETURN r.id AS resource_id,
           r.name AS resource_name,
           r.sensitivity AS sensitivity,
           r.environment AS environment,
           count(DISTINCT e) AS offboarded_reach_count
    ORDER BY offboarded_reach_count DESC, r.sensitivity ASC
    LIMIT 5
    """
    top_risky = [dict(rec) for rec in tx.run(risky_cypher)]

    return {
        "total_employees": emp_stats["total"],
        "active_employees": emp_stats["active"],
        "offboarded_employees": emp_stats["offboarded"],
        "ghost_chains_count": ghost_stats["ghost_chains_count"],
        "ghost_resources_count": ghost_stats["ghost_resources_count"],
        "top_risky_resources": top_risky
    }


# 5. Get All Employees with Search & Filter
def query_all_employees(tx, search: str = "", status_filter: str = "all") -> List[Dict[str, Any]]:
    if tx is None:
        data = load_fallback_data()
        results = []
        for e in data.get("employees", []):
            if status_filter != "all" and e.get("status") != status_filter:
                continue
            if search:
                s = search.lower()
                if s not in e.get("name", "").lower() and s not in e.get("email", "").lower() and s not in e.get("department", "").lower():
                    continue
            br = query_employee_blast_radius(None, e["id"])
            res_count = sum(1 for n in br.get("nodes", []) if n.get("type") == "CloudResource")
            results.append({
                "id": e["id"],
                "name": e["name"],
                "email": e["email"],
                "department": e["department"],
                "status": e["status"],
                "offboarded_at": e.get("offboarded_at"),
                "reachable_resources_count": res_count
            })
        return results

    cypher = """
    MATCH (e:Employee)
    WHERE ($status = 'all' OR e.status = $status)
      AND ($search = '' OR toLower(e.name) CONTAINS toLower($search) OR toLower(e.email) CONTAINS toLower($search) OR toLower(e.department) CONTAINS toLower($search))
    OPTIONAL MATCH (e)-[:MEMBER_OF|MIRRORS|GRANTS_ROLE|CAN_ACCESS|DIRECTLY_ACCESSES*1..6]->(r:CloudResource)
    RETURN e.id AS id,
           e.name AS name,
           e.email AS email,
           e.department AS department,
           e.status AS status,
           e.offboarded_at AS offboarded_at,
           count(DISTINCT r) AS reachable_resources_count
    ORDER BY e.status DESC, e.name ASC
    """
    result = tx.run(cypher, search=search, status=status_filter)
    return [dict(record) for record in result]


# 6. Full Graph Data for Vis-Network Explorer
def query_full_graph_data(tx) -> Dict[str, Any]:
    if tx is None:
        data = load_fallback_data()
        nodes = []
        edges = []

        for emp in data.get("employees", []):
            nodes.append({"id": emp["id"], "name": emp["name"], "type": "Employee", "status": emp["status"], "department": emp["department"]})
        for sg in data.get("slack_groups", []):
            nodes.append({"id": sg["id"], "name": sg["name"], "type": "SlackGroup"})
        for og in data.get("okta_groups", []):
            nodes.append({"id": og["id"], "name": og["name"], "type": "OktaGroup"})
        for ar in data.get("aws_roles", []):
            nodes.append({"id": ar["id"], "name": ar["name"], "type": "AWSRole"})
        for cr in data.get("cloud_resources", []):
            nodes.append({"id": cr["id"], "name": cr["name"], "type": "CloudResource", "sensitivity": cr["sensitivity"], "environment": cr["environment"]})

        for rel in data.get("emp_slack", []):
            edges.append({"id": f"e-{rel['emp_id']}-MEMBER_OF-{rel['slack_id']}", "from": rel["emp_id"], "to": rel["slack_id"], "label": "MEMBER_OF"})
        for rel in data.get("slack_okta", []):
            edges.append({"id": f"e-{rel['slack_id']}-MIRRORS-{rel['okta_id']}", "from": rel["slack_id"], "to": rel["okta_id"], "label": "MIRRORS"})
        for rel in data.get("emp_okta", []):
            edges.append({"id": f"e-{rel['emp_id']}-MEMBER_OF-{rel['okta_id']}", "from": rel["emp_id"], "to": rel["okta_id"], "label": "MEMBER_OF"})
        for rel in data.get("okta_role", []):
            edges.append({"id": f"e-{rel['okta_id']}-GRANTS_ROLE-{rel['role_id']}", "from": rel["okta_id"], "to": rel["role_id"], "label": "GRANTS_ROLE"})
        for rel in data.get("role_resource", []):
            edges.append({"id": f"e-{rel['role_id']}-CAN_ACCESS-{rel['resource_id']}", "from": rel["role_id"], "to": rel["resource_id"], "label": "CAN_ACCESS"})
        for rel in data.get("emp_direct", []):
            edges.append({"id": f"e-{rel['emp_id']}-DIRECTLY_ACCESSES-{rel['resource_id']}", "from": rel["emp_id"], "to": rel["resource_id"], "label": "DIRECTLY_ACCESSES"})

        return {"nodes": nodes, "edges": edges}

    cypher = """
    MATCH (n)
    OPTIONAL MATCH (n)-[r]->(m)
    WITH collect(DISTINCT n) AS all_nodes, collect(DISTINCT r) AS all_rels
    RETURN [n IN all_nodes | {
        id: n.id,
        name: coalesce(n.name, n.id),
        type: labels(n)[0],
        status: n.status,
        environment: n.environment,
        sensitivity: n.sensitivity,
        department: n.department
    }] AS nodes,
    [r IN all_rels WHERE r IS NOT NULL | {
        id: startNode(r).id + "-" + type(r) + "-" + endNode(r).id,
        from: startNode(r).id,
        to: endNode(r).id,
        label: type(r)
    }] AS edges
    """
    result = tx.run(cypher)
    single = result.single()
    if single:
        return {"nodes": single["nodes"], "edges": single["edges"]}
    return {"nodes": [], "edges": []}
