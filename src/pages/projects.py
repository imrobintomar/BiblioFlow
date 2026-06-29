import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State

from services.event_service import EventService
from services.project_service import ProjectService

dash.register_page(__name__, path="/projects", name="Projects")

_projects = ProjectService()
_events = EventService()


def _project_card(project: dict) -> html.Div:
    return html.Div(
        className="panel-card",
        children=[
            html.Div(
                style={"display": "flex", "gap": "8px", "alignItems": "center"},
                children=[
                    dcc.Input(
                        id={"type": "project-name-input", "id": project["id"]},
                        value=project["name"],
                        className="search-input",
                        style={"flex": 1},
                    ),
                    html.Button(
                        "Save",
                        id={"type": "project-rename-btn", "id": project["id"]},
                        className="btn btn-sm btn-outline-light",
                    ),
                    html.Button(
                        "Delete",
                        id={"type": "project-delete-btn", "id": project["id"]},
                        className="btn btn-sm btn-outline-danger",
                    ),
                ],
            ),
            html.P(f"{project['paper_count']} paper(s)", style={"color": "#5483B3", "marginTop": "8px"}),
            html.P(f"Created {project['created_at']}", style={"color": "#5483B3", "fontSize": "12px"}),
        ],
    )


def layout():
    projects = _projects.list_projects()
    events = _events.recent(limit=10)
    event_rows = [
        html.P(
            f"{e['timestamp']} — {e['type']} ({e['status']}): {e['message']}",
            style={"color": "#5483B3", "fontSize": "13px"},
        )
        for e in events
    ] or [html.P("No activity yet.", className="coming-soon")]

    return html.Div(
        [
            html.H3("Projects"),
            html.Div(
                style={"display": "flex", "gap": "8px", "margin": "16px 0"},
                children=[
                    dcc.Input(id="new-project-name", placeholder="New project name", className="search-input"),
                    html.Button("Create Project", id="create-project-btn", className="btn btn-primary"),
                ],
            ),
            html.Div(id="project-action-feedback"),
            html.Div(id="project-list", children=[_project_card(p) for p in projects]),
            html.Div(
                className="panel-card",
                children=[html.H5("Recent Activity"), *event_rows],
            ),
        ]
    )


@dash.callback(
    Output("project-list", "children"),
    Output("project-action-feedback", "children"),
    Input("create-project-btn", "n_clicks"),
    State("new-project-name", "value"),
    prevent_initial_call=True,
)
def create_project(n_clicks, name):
    if not name or not name.strip():
        return [_project_card(p) for p in _projects.list_projects()], html.P(
            "Enter a project name first.", style={"color": "#B3261E"}
        )
    try:
        _projects.create(name.strip())
    except Exception:  # noqa: BLE001
        return [_project_card(p) for p in _projects.list_projects()], html.P(
            f"A project named '{name.strip()}' already exists.", style={"color": "#B3261E"}
        )
    return [_project_card(p) for p in _projects.list_projects()], html.P(
        f"Created '{name.strip()}'.", style={"color": "#3F8F66"}
    )


@dash.callback(
    Output("project-list", "children", allow_duplicate=True),
    Input({"type": "project-delete-btn", "id": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def delete_project(n_clicks_list):
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks_list):
        return dash.no_update
    triggered_id = ctx.triggered_id
    if triggered_id and triggered_id.get("type") == "project-delete-btn":
        _projects.delete(triggered_id["id"])
    return [_project_card(p) for p in _projects.list_projects()]


@dash.callback(
    Output("project-list", "children", allow_duplicate=True),
    Input({"type": "project-rename-btn", "id": dash.ALL}, "n_clicks"),
    State({"type": "project-name-input", "id": dash.ALL}, "value"),
    State({"type": "project-name-input", "id": dash.ALL}, "id"),
    prevent_initial_call=True,
)
def rename_project(n_clicks_list, names, ids):
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks_list):
        return dash.no_update
    triggered_id = ctx.triggered_id
    if triggered_id and triggered_id.get("type") == "project-rename-btn":
        for input_id, name in zip(ids, names):
            if input_id["id"] == triggered_id["id"] and name and name.strip():
                try:
                    _projects.rename(triggered_id["id"], name.strip())
                except Exception:  # noqa: BLE001
                    pass
    return [_project_card(p) for p in _projects.list_projects()]
