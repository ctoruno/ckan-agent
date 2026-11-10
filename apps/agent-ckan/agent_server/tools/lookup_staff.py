import asyncio
import os
import re
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementParameterListItem, StatementState
from langchain_core.tools import tool

STAFF_TABLE = "idb_rsd_catalog.datahub_utils.data_pr"
PENDING_STATES = {StatementState.PENDING, StatementState.RUNNING}
POLL_INTERVAL_SECONDS = 2
MAX_WAIT_SECONDS = 180
EMAIL_FORMAT = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# The email is bound as a parameter, never interpolated, so user input can't alter the query.
LOOKUP_STAFF_QUERY = f"""
SELECT employee_number, full_name
FROM {STAFF_TABLE}
WHERE lower(trim(email)) = :email OR lower(trim(email_id)) = :email
"""


@tool
async def lookup_staff(email: str) -> dict[str, Any]:
    """Resolve one IDB staff member by exact email address.

    Returns `{employee_code, display_name, email}` or `{"status": "not_found"}`. There is no
    search by name: if the email doesn't resolve, ask the user to check it.

    Args:
        email: The email address to look up, e.g. "jdoe@iadb.org".
    """
    warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID")
    if not warehouse_id:
        return {"error": "DATABRICKS_WAREHOUSE_ID is not configured."}

    normalized_email = email.strip().lower()
    if not EMAIL_FORMAT.match(normalized_email):
        return {"error": f"'{email}' is not a valid email address."}

    statement_execution = WorkspaceClient().statement_execution
    # The SDK client is synchronous; run it in a thread so the event loop isn't blocked.
    response = await asyncio.to_thread(
        statement_execution.execute_statement,
        statement=LOOKUP_STAFF_QUERY,
        warehouse_id=warehouse_id,
        parameters=[StatementParameterListItem(name="email", value=normalized_email)],
        wait_timeout="30s",
    )

    # A cold warehouse can take longer than the initial wait to start, so keep polling.
    deadline = asyncio.get_running_loop().time() + MAX_WAIT_SECONDS
    while response.status and response.status.state in PENDING_STATES:
        if asyncio.get_running_loop().time() > deadline:
            await asyncio.to_thread(statement_execution.cancel_execution, response.statement_id)
            return {"error": f"The staff lookup timed out after {MAX_WAIT_SECONDS} seconds."}
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
        response = await asyncio.to_thread(statement_execution.get_statement, response.statement_id)

    state = response.status.state if response.status else None
    if state != StatementState.SUCCEEDED:
        error = response.status.error if response.status else None
        message = error.message if error and error.message else f"Query did not succeed (state: {state})."
        return {"error": message}

    rows = (response.result.data_array if response.result else None) or []
    # The same person can appear in several rows; only distinct (employee_number, full_name) count.
    matches = {(employee_number, full_name) for employee_number, full_name in rows}
    if not matches:
        return {"status": "not_found"}
    if len(matches) > 1:
        return {"error": "This email matches more than one staff member. Ask the user for a different email."}
    employee_code, display_name = matches.pop()
    return {"employee_code": employee_code, "display_name": display_name, "email": normalized_email}
