#!/usr/bin/env python3
"""
Notion API Handler for Claude Code
Supports: Database, Page, Block, Search operations
"""

import os
import sys
import json
import argparse
import requests
from typing import Optional, Dict, Any, List

# Configuration
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# 계정(account) → 토큰이 담긴 환경변수 이름
#   personal = 기본 계정 / second = 두 번째 계정
# 두 토큰 모두 zshrc에 정적 통합 토큰으로 상주하므로 재인증 불필요.
ACCOUNT_TOKEN_ENV = {
    "personal": "NOTION_TOKEN",
    "second": "NOTION_TOKEN_SECOND",
}
_SELECTED_ACCOUNT = "personal"


def get_headers() -> Dict[str, str]:
    """Get API headers with token from environment.

    --account 플래그로 선택된 계정의 토큰을 사용한다
    (personal=NOTION_TOKEN, second=NOTION_TOKEN_SECOND).
    """
    env_name = ACCOUNT_TOKEN_ENV.get(_SELECTED_ACCOUNT, "NOTION_TOKEN")
    token = os.environ.get(env_name)
    if not token:
        print(f"Error: {env_name} environment variable not set "
              f"(account={_SELECTED_ACCOUNT})", file=sys.stderr)
        sys.exit(1)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }


def format_id(id_str: str) -> str:
    """Format page/database ID (remove hyphens if present)."""
    return id_str.replace("-", "")


def _is_phone_number(value: str) -> bool:
    """Check if value looks like a Korean phone number."""
    # Remove hyphens for checking
    digits = value.replace("-", "").replace(" ", "")
    # Korean mobile: 010xxxxxxxx (10-11 digits starting with 010)
    if digits.startswith("010") and len(digits) in [10, 11]:
        return True
    # Korean landline: 02xxxxxxxx, 031xxxxxxxx, etc.
    if digits.startswith("0") and len(digits) in [9, 10, 11] and digits.isdigit():
        return True
    return False


def parse_properties_schema(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert simplified property schema to Notion API format.

    Input formats:
    - "title" -> title property
    - "rich_text" -> rich_text property
    - "number" -> number property
    - "checkbox" -> checkbox property
    - "date" -> date property
    - "email" -> email property
    - "phone_number" -> phone_number property
    - "url" -> url property
    - {"select": ["opt1", "opt2"]} -> select with options
    - {"multi_select": ["opt1", "opt2"]} -> multi_select with options
    """
    result = {}
    for name, prop in properties.items():
        if isinstance(prop, str):
            # Simple type
            result[name] = {prop: {}}
        elif isinstance(prop, dict):
            # Complex type with options
            if "select" in prop:
                options = [{"name": opt} for opt in prop["select"]]
                result[name] = {"select": {"options": options}}
            elif "multi_select" in prop:
                options = [{"name": opt} for opt in prop["multi_select"]]
                result[name] = {"multi_select": {"options": options}}
            else:
                result[name] = prop
    return result


# DB 스키마 캐시: {database_id(하이픈 제거) -> {속성명: 타입}}
_SCHEMA_CACHE: Dict[str, Dict[str, str]] = {}


def fetch_db_schema(database_id: str) -> Dict[str, str]:
    """대상 DB의 {속성명: 타입} 맵을 조회한다. 실패하면 빈 dict(=휴리스틱 폴백).

    속성명이 DB마다 다르므로(이름/업무/Name…) 이름으로 타입을 추측하면 안 된다.
    실제 스키마를 읽어 타입을 확정하는 것이 유일하게 안전한 방법이다.
    """
    key = format_id(database_id)
    if key in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[key]
    try:
        resp = requests.get(f"{NOTION_API_BASE}/databases/{key}",
                            headers=get_headers(), timeout=20)
        data = resp.json()
        props = data.get("properties") or {}
        schema = {name: meta.get("type") for name, meta in props.items()
                  if isinstance(meta, dict)}
    except Exception:
        schema = {}
    _SCHEMA_CACHE[key] = schema
    return schema


def _as_text_chunks(value: Any) -> List[Dict]:
    return [{"text": {"content": str(value)}}]


def _build_by_type(prop_type: str, value: Any) -> Optional[Dict[str, Any]]:
    """Notion 속성 타입에 맞춰 값을 변환한다. 지원하지 않는 타입이면 None."""
    if prop_type == "title":
        return {"title": _as_text_chunks(value)}
    if prop_type == "rich_text":
        return {"rich_text": _as_text_chunks(value)}
    if prop_type == "number":
        try:
            return {"number": float(value) if value not in (None, "") else None}
        except (TypeError, ValueError):
            return {"number": None}
    if prop_type == "checkbox":
        if isinstance(value, str):
            return {"checkbox": value.strip().lower() in ("true", "y", "yes", "1", "체크", "완료")}
        return {"checkbox": bool(value)}
    if prop_type == "select":
        return {"select": None if value in (None, "") else {"name": str(value)}}
    if prop_type == "status":
        return {"status": None if value in (None, "") else {"name": str(value)}}
    if prop_type == "multi_select":
        vals = value if isinstance(value, list) else [value]
        return {"multi_select": [{"name": str(v)} for v in vals if v not in (None, "")]}
    if prop_type == "date":
        if isinstance(value, dict):
            return {"date": value}
        if value in (None, ""):
            return {"date": None}
        return {"date": {"start": str(value)}}
    if prop_type == "url":
        return {"url": str(value) if value else None}
    if prop_type == "email":
        return {"email": str(value) if value else None}
    if prop_type == "phone_number":
        return {"phone_number": str(value) if value else None}
    if prop_type == "people":
        vals = value if isinstance(value, list) else [value]
        return {"people": [{"object": "user", "id": str(v)} for v in vals if v]}
    if prop_type == "relation":
        vals = value if isinstance(value, list) else [value]
        return {"relation": [{"id": format_id(str(v))} for v in vals if v]}
    if prop_type == "files":
        vals = value if isinstance(value, list) else [value]
        return {"files": [{"type": "external", "name": str(v),
                           "external": {"url": str(v)}} for v in vals if v]}
    # formula/rollup/created_time 등은 쓰기 불가 → 건너뛴다
    return None


def _guess_property(name: str, value: Any) -> Dict[str, Any]:
    """스키마를 못 읽었을 때의 폴백 추측. 정확하지 않으므로 최후 수단이다."""
    if name in ("이름", "Name", "제목", "Title"):
        return {"title": _as_text_chunks(value)}
    if isinstance(value, bool):
        return {"checkbox": value}
    if isinstance(value, (int, float)):
        return {"number": value}
    if isinstance(value, list):
        return {"multi_select": [{"name": str(v)} for v in value]}
    if isinstance(value, str):
        if "@" in value and "." in value:
            return {"email": value}
        if name == "연락처" or _is_phone_number(value):
            return {"phone_number": value}
        if value.startswith("http"):
            return {"url": value}
        if len(value) == 10 and value[4] == "-" and value[7] == "-":
            return {"date": {"start": value}}
    return {"rich_text": _as_text_chunks(value)}


def parse_page_properties(properties: Dict[str, Any],
                          schema: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    간단한 값을 Notion API 형식으로 변환한다.

    schema({속성명: 타입})가 주어지면 **그 타입을 그대로 따른다**. 이게 정답 경로다.
    schema가 없을 때만 이름·값 모양으로 추측한다(폴백).

    입력 예:
      "text value" · 123 · true/false · "2025-01-01" · ["opt1","opt2"] · "option"
    """
    result: Dict[str, Any] = {}
    unknown: List[str] = []
    for name, value in properties.items():
        prop_type = (schema or {}).get(name)
        if prop_type:
            built = _build_by_type(prop_type, value)
            if built is not None:
                result[name] = built
            # 쓰기 불가 타입(formula/rollup 등)은 조용히 건너뛴다
            continue
        if schema:
            # 스키마는 읽었는데 그 안에 없는 속성명 → 오타일 가능성이 높다
            unknown.append(name)
            continue
        result[name] = _guess_property(name, value)

    if unknown:
        print(f"Warning: DB에 없는 속성명 {unknown} — 건너뜀. "
              f"사용 가능: {sorted((schema or {}).keys())}", file=sys.stderr)
    return result


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

def create_database(parent_id: str, title: str, properties: Dict[str, Any]) -> Dict:
    """Create a new database under the specified parent page."""
    url = f"{NOTION_API_BASE}/databases"

    # Parse properties to Notion format
    notion_properties = parse_properties_schema(properties)

    payload = {
        "parent": {"type": "page_id", "page_id": format_id(parent_id)},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": notion_properties
    }

    response = requests.post(url, headers=get_headers(), json=payload)
    return response.json()


def get_database(database_id: str) -> Dict:
    """Get database information."""
    url = f"{NOTION_API_BASE}/databases/{format_id(database_id)}"
    response = requests.get(url, headers=get_headers())
    return response.json()


def query_database(database_id: str, filter_obj: Optional[Dict] = None,
                   sorts: Optional[List] = None) -> Dict:
    """Query database with optional filter and sorts."""
    url = f"{NOTION_API_BASE}/databases/{format_id(database_id)}/query"

    payload = {}
    if filter_obj:
        payload["filter"] = filter_obj
    if sorts:
        payload["sorts"] = sorts

    response = requests.post(url, headers=get_headers(), json=payload)
    return response.json()


def update_database(database_id: str, properties: Optional[Dict] = None,
                    title: Optional[str] = None) -> Dict:
    """Update database properties or title."""
    url = f"{NOTION_API_BASE}/databases/{format_id(database_id)}"

    payload = {}
    if title:
        payload["title"] = [{"type": "text", "text": {"content": title}}]
    if properties:
        payload["properties"] = parse_properties_schema(properties)

    response = requests.patch(url, headers=get_headers(), json=payload)
    return response.json()


# =============================================================================
# PAGE OPERATIONS
# =============================================================================

def create_page(parent_id: str, properties: Dict[str, Any],
                children: Optional[List] = None, is_database: bool = True) -> Dict:
    """Create a new page (as database item or standalone page)."""
    url = f"{NOTION_API_BASE}/pages"

    schema = None
    if is_database:
        parent = {"type": "database_id", "database_id": format_id(parent_id)}
        # 속성명은 DB마다 다르다(이름/업무/Name…). 추측하지 말고 실제 스키마를 읽는다.
        schema = fetch_db_schema(parent_id) or None
    else:
        parent = {"type": "page_id", "page_id": format_id(parent_id)}

    payload = {
        "parent": parent,
        "properties": parse_page_properties(properties, schema)
    }

    if children:
        payload["children"] = children

    response = requests.post(url, headers=get_headers(), json=payload)
    return response.json()


def get_page(page_id: str) -> Dict:
    """Get page information."""
    url = f"{NOTION_API_BASE}/pages/{format_id(page_id)}"
    response = requests.get(url, headers=get_headers())
    return response.json()


def update_page(page_id: str, properties: Dict[str, Any]) -> Dict:
    """Update page properties.

    페이지가 DB 항목이면 부모 DB 스키마를 읽어 타입을 확정한다.
    """
    url = f"{NOTION_API_BASE}/pages/{format_id(page_id)}"

    schema = None
    try:
        page = get_page(page_id)
        parent = page.get("parent") or {}
        if parent.get("type") == "database_id":
            schema = fetch_db_schema(parent["database_id"]) or None
    except Exception:
        schema = None

    payload = {
        "properties": parse_page_properties(properties, schema)
    }

    response = requests.patch(url, headers=get_headers(), json=payload)
    return response.json()


def archive_page(page_id: str, archived: bool = True) -> Dict:
    """Archive (delete) a page."""
    url = f"{NOTION_API_BASE}/pages/{format_id(page_id)}"

    payload = {"archived": archived}

    response = requests.patch(url, headers=get_headers(), json=payload)
    return response.json()


# =============================================================================
# BLOCK OPERATIONS
# =============================================================================

def parse_blocks(blocks: List[Dict]) -> List[Dict]:
    """
    Convert simplified block format to Notion API format.

    Input formats:
    - {"type": "heading_1", "text": "Title"}
    - {"type": "heading_2", "text": "Subtitle"}
    - {"type": "heading_3", "text": "Section"}
    - {"type": "paragraph", "text": "Content"}
    - {"type": "bulleted_list_item", "text": "Item"}
    - {"type": "numbered_list_item", "text": "Item"}
    - {"type": "to_do", "text": "Task", "checked": false}
    - {"type": "divider"}
    - {"type": "image", "url": "https://..."} (external image)
    - {"type": "bookmark", "url": "https://..."}
    - {"type": "quote", "text": "Quote text"}
    - {"type": "callout", "text": "Callout text", "emoji": "💡"}
    - {"type": "code", "text": "code here", "language": "python"}
    - {"type": "toggle", "text": "Toggle title"}
    """
    result = []
    for block in blocks:
        block_type = block.get("type", "paragraph")

        if block_type == "divider":
            result.append({"object": "block", "type": "divider", "divider": {}})

        elif block_type == "image":
            # External image
            result.append({
                "object": "block",
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {
                        "url": block.get("url", "")
                    }
                }
            })

        elif block_type == "bookmark":
            # Bookmark (link preview)
            result.append({
                "object": "block",
                "type": "bookmark",
                "bookmark": {
                    "url": block.get("url", "")
                }
            })

        elif block_type == "quote":
            # Quote block
            result.append({
                "object": "block",
                "type": "quote",
                "quote": {
                    "rich_text": [{"type": "text", "text": {"content": block.get("text", "")}}]
                }
            })

        elif block_type == "callout":
            # Callout with emoji icon
            callout_content = {
                "rich_text": [{"type": "text", "text": {"content": block.get("text", "")}}]
            }
            if block.get("emoji"):
                callout_content["icon"] = {"type": "emoji", "emoji": block.get("emoji")}
            result.append({
                "object": "block",
                "type": "callout",
                "callout": callout_content
            })

        elif block_type == "code":
            # Code block with language
            result.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": block.get("text", "")}}],
                    "language": block.get("language", "plain text")
                }
            })

        elif block_type == "toggle":
            # Toggle block (can have children)
            result.append({
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": block.get("text", "")}}]
                }
            })

        elif block_type in ["heading_1", "heading_2", "heading_3", "paragraph",
                           "bulleted_list_item", "numbered_list_item"]:
            result.append({
                "object": "block",
                "type": block_type,
                block_type: {
                    "rich_text": [{"type": "text", "text": {"content": block.get("text", "")}}]
                }
            })

        elif block_type == "to_do":
            result.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": block.get("text", "")}}],
                    "checked": block.get("checked", False)
                }
            })
    return result


def append_blocks(block_id: str, children: List[Dict]) -> Dict:
    """Append blocks to a page or block."""
    url = f"{NOTION_API_BASE}/blocks/{format_id(block_id)}/children"

    payload = {
        "children": parse_blocks(children)
    }

    response = requests.patch(url, headers=get_headers(), json=payload)
    return response.json()


def get_blocks(block_id: str) -> Dict:
    """Get child blocks of a page or block."""
    url = f"{NOTION_API_BASE}/blocks/{format_id(block_id)}/children"
    response = requests.get(url, headers=get_headers())
    return response.json()


def update_block(block_id: str, content: Dict) -> Dict:
    """Update a block's content."""
    url = f"{NOTION_API_BASE}/blocks/{format_id(block_id)}"
    response = requests.patch(url, headers=get_headers(), json=content)
    return response.json()


def delete_block(block_id: str) -> Dict:
    """Delete a block."""
    url = f"{NOTION_API_BASE}/blocks/{format_id(block_id)}"
    response = requests.delete(url, headers=get_headers())
    return response.json()


def delete_blocks(block_ids: List[str]) -> List[Dict]:
    """Delete multiple blocks."""
    results = []
    for block_id in block_ids:
        result = delete_block(block_id)
        results.append({"id": block_id, "result": result})
    return results


def get_all_blocks(block_id: str, recursive: bool = False) -> List[Dict]:
    """
    Get all child blocks with pagination support.
    If recursive=True, also fetches children of children.
    """
    all_blocks = []
    start_cursor = None

    while True:
        url = f"{NOTION_API_BASE}/blocks/{format_id(block_id)}/children"
        params = {}
        if start_cursor:
            params["start_cursor"] = start_cursor

        response = requests.get(url, headers=get_headers(), params=params)
        data = response.json()

        if "results" in data:
            for block in data["results"]:
                all_blocks.append(block)
                # Recursively fetch children if needed
                if recursive and block.get("has_children"):
                    child_blocks = get_all_blocks(block["id"], recursive=True)
                    block["children"] = child_blocks

        if not data.get("has_more"):
            break
        start_cursor = data.get("next_cursor")

    return all_blocks


def clear_page(page_id: str) -> Dict:
    """Delete all blocks from a page."""
    blocks = get_all_blocks(page_id)
    block_ids = [b["id"] for b in blocks]
    if block_ids:
        results = delete_blocks(block_ids)
        return {"deleted_count": len(block_ids), "results": results}
    return {"deleted_count": 0, "message": "No blocks to delete"}


# =============================================================================
# SEARCH
# =============================================================================

def search(query: str, filter_type: Optional[str] = None) -> Dict:
    """
    Search Notion workspace.
    filter_type: "page" or "database"
    """
    url = f"{NOTION_API_BASE}/search"

    payload = {"query": query}
    if filter_type:
        payload["filter"] = {"value": filter_type, "property": "object"}

    response = requests.post(url, headers=get_headers(), json=payload)
    return response.json()


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Notion API Handler")
    parser.add_argument(
        "--account", choices=["personal", "second"], default="personal",
        help="사용할 Notion 계정/토큰 (personal=NOTION_TOKEN, "
             "second=NOTION_TOKEN_SECOND). 기본: personal. "
             "서브커맨드 앞에 위치시킬 것.")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Database commands
    create_db_parser = subparsers.add_parser("create-db", help="Create database")
    create_db_parser.add_argument("--parent", required=True, help="Parent page ID")
    create_db_parser.add_argument("--title", required=True, help="Database title")
    create_db_parser.add_argument("--properties", required=True, help="Properties JSON")

    get_db_parser = subparsers.add_parser("get-db", help="Get database info")
    get_db_parser.add_argument("--id", required=True, help="Database ID")

    query_db_parser = subparsers.add_parser("query-db", help="Query database")
    query_db_parser.add_argument("--id", required=True, help="Database ID")
    query_db_parser.add_argument("--filter", help="Filter JSON")
    query_db_parser.add_argument("--sorts", help="Sorts JSON")

    update_db_parser = subparsers.add_parser("update-db", help="Update database")
    update_db_parser.add_argument("--id", required=True, help="Database ID")
    update_db_parser.add_argument("--properties", help="Properties JSON")
    update_db_parser.add_argument("--title", help="New title")

    # Page commands
    create_page_parser = subparsers.add_parser("create-page", help="Create page")
    create_page_parser.add_argument("--parent", required=True, help="Parent DB/page ID")
    create_page_parser.add_argument("--properties", required=True, help="Properties JSON")
    create_page_parser.add_argument("--children", help="Children blocks JSON")
    create_page_parser.add_argument("--standalone", action="store_true", help="Create as standalone page (not DB item)")

    get_page_parser = subparsers.add_parser("get-page", help="Get page info")
    get_page_parser.add_argument("--id", required=True, help="Page ID")

    update_page_parser = subparsers.add_parser("update-page", help="Update page")
    update_page_parser.add_argument("--id", required=True, help="Page ID")
    update_page_parser.add_argument("--properties", required=True, help="Properties JSON")

    archive_page_parser = subparsers.add_parser("archive-page", help="Archive page")
    archive_page_parser.add_argument("--id", required=True, help="Page ID")

    # Block commands
    append_blocks_parser = subparsers.add_parser("append-blocks", help="Append blocks")
    append_blocks_parser.add_argument("--id", required=True, help="Page/block ID")
    append_blocks_parser.add_argument("--blocks", required=True, help="Blocks JSON")

    get_blocks_parser = subparsers.add_parser("get-blocks", help="Get blocks")
    get_blocks_parser.add_argument("--id", required=True, help="Page/block ID")

    get_all_blocks_parser = subparsers.add_parser("get-all-blocks", help="Get all blocks with pagination")
    get_all_blocks_parser.add_argument("--id", required=True, help="Page/block ID")
    get_all_blocks_parser.add_argument("--recursive", action="store_true", help="Include nested children")

    update_block_parser = subparsers.add_parser("update-block", help="Update a block")
    update_block_parser.add_argument("--id", required=True, help="Block ID")
    update_block_parser.add_argument("--content", required=True, help="Block content JSON")

    delete_block_parser = subparsers.add_parser("delete-block", help="Delete a block")
    delete_block_parser.add_argument("--id", required=True, help="Block ID")

    delete_blocks_parser = subparsers.add_parser("delete-blocks", help="Delete multiple blocks")
    delete_blocks_parser.add_argument("--ids", required=True, help="Block IDs JSON array")

    clear_page_parser = subparsers.add_parser("clear-page", help="Delete all blocks from a page")
    clear_page_parser.add_argument("--id", required=True, help="Page ID")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search workspace")
    search_parser.add_argument("--query", required=True, help="Search query")
    search_parser.add_argument("--type", choices=["page", "database"], help="Filter by type")

    args = parser.parse_args()

    global _SELECTED_ACCOUNT
    _SELECTED_ACCOUNT = args.account

    if not args.command:
        parser.print_help()
        sys.exit(1)

    result = None

    # Execute command
    if args.command == "create-db":
        props = json.loads(args.properties)
        result = create_database(args.parent, args.title, props)

    elif args.command == "get-db":
        result = get_database(args.id)

    elif args.command == "query-db":
        filter_obj = json.loads(args.filter) if args.filter else None
        sorts = json.loads(args.sorts) if args.sorts else None
        result = query_database(args.id, filter_obj, sorts)

    elif args.command == "update-db":
        props = json.loads(args.properties) if args.properties else None
        result = update_database(args.id, props, args.title)

    elif args.command == "create-page":
        props = json.loads(args.properties)
        children = json.loads(args.children) if args.children else None
        result = create_page(args.parent, props, children, not args.standalone)

    elif args.command == "get-page":
        result = get_page(args.id)

    elif args.command == "update-page":
        props = json.loads(args.properties)
        result = update_page(args.id, props)

    elif args.command == "archive-page":
        result = archive_page(args.id)

    elif args.command == "append-blocks":
        blocks = json.loads(args.blocks)
        result = append_blocks(args.id, blocks)

    elif args.command == "get-blocks":
        result = get_blocks(args.id)

    elif args.command == "get-all-blocks":
        blocks = get_all_blocks(args.id, args.recursive)
        result = {"blocks": blocks, "count": len(blocks)}

    elif args.command == "update-block":
        content = json.loads(args.content)
        result = update_block(args.id, content)

    elif args.command == "delete-block":
        result = delete_block(args.id)

    elif args.command == "delete-blocks":
        block_ids = json.loads(args.ids)
        result = delete_blocks(block_ids)

    elif args.command == "clear-page":
        result = clear_page(args.id)

    elif args.command == "search":
        result = search(args.query, args.type)

    # Output result
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
