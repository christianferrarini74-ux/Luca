"""Executable address/action contracts, without behavioral prompt instructions."""


def navigation_schema(state):
    def variant(properties, required):
        return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}

    variants = [variant({"action": {"const": "search", "type": "string"},
                         "query": {"type": "string"}}, ["action", "query"])]
    local = set(state.get("local_target_ids", ()))
    # Deduplicate addresses already reachable through the complete fast directory.
    global_ids = {item["id"] for item in state.get("global_candidates", ())} - local - {state.get("reading_id")}
    for source, ids in (("local", local), ("global", global_ids)):
        if ids:
            variants.append(variant({"action": {"const": "open", "type": "string"},
                "source": {"const": source, "type": "string"},
                "target_id": {"type": "integer", "enum": sorted(ids)}}, ["action", "source", "target_id"]))
    variants.append(variant({"action": {"const": "answer", "type": "string"},
        "use_memory": {"type": "boolean"}, "response": {"type": "string"}}, ["action", "use_memory", "response"]))
    return {"anyOf": variants}
