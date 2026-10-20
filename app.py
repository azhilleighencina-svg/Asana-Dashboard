import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__)

ASANA_TOKEN = "2/1213131775290440/1219531181409366:221d8028111f6f123dc436a63d79d2d0"
PORTFOLIO_GID = "1218357020346610"
HEADERS = {"Authorization": f"Bearer {ASANA_TOKEN}"}


def fetch_asana_matrix():
  # 1. Fetch all project items inside the "IT BSP Daily Time Record" Portfolio
  portfolio_url = f"https://app.asana.com/api/1.0/portfolios/{PORTFOLIO_GID}/items?opt_fields=name"
  res = requests.get(portfolio_url, headers=HEADERS)

  if res.status_code != 200:
    return {
        "error": True,
        "message": (
            f"Portfolio API Error ({res.status_code}): {res.text}. Verify token"
            " access to this portfolio."
        ),
    }

  projects = res.json().get("data", [])
  if not projects:
    return {
        "error": True,
        "message": (
            "Connected to Portfolio 'IT BSP Daily Time Record', but no member"
            " projects were found inside it."
        ),
    }

  matrix = {}
  member_totals = {}

  # 2. Loop through each project (Project Name = Team Member Name)
  for proj in projects:
    member_name = proj.get("name", "").strip()
    proj_gid = proj.get("gid")

    if not member_name or not proj_gid:
      continue

    matrix[member_name] = {
        "Operations & Support": 0.0,
        "Project Delivery": 0.0,
    }

    # Fetch tasks inside this member's project
    tasks_url = f"https://app.asana.com/api/1.0/projects/{proj_gid}/tasks?opt_fields=name,custom_fields"
    t_res = requests.get(tasks_url, headers=HEADERS)

    if t_res.status_code != 200:
      continue

    tasks = t_res.json().get("data", [])

    # 3. Process each task inside the member's project
    for task in tasks:
      manhours = 0.0
      has_project_ref = False

      for field in task.get("custom_fields", []):
        f_name = field.get("name", "").strip().lower()

        # Extract Manhours
        if "hour" in f_name or "manhour" in f_name:
          if field.get("number_value") is not None:
            manhours = float(field["number_value"])
          elif field.get("display_value"):
            try:
              manhours = float(field["display_value"])
            except ValueError:
              pass

        # Check "Project Ref" rule
        if "project ref" in f_name or f_name == "project reference":
          val = (
              field.get("display_value")
              or field.get("text_value")
              or field.get("number_value")
          )
          if val is not None and str(val).strip() != "":
            has_project_ref = True

      # Apply classification rule:
      # Project Ref blank = Operations & Support
      # Project Ref has value/reference = Projects (Project Delivery)
      if has_project_ref:
        matrix[member_name]["Project Delivery"] += manhours
      else:
        matrix[member_name]["Operations & Support"] += manhours

    member_totals[member_name] = (
        matrix[member_name]["Operations & Support"]
        + matrix[member_name]["Project Delivery"]
    )

  # Sort assignees by total manhours descending (highest at the top/left)
  sorted_assignees = sorted(
      matrix.keys(), key=lambda name: member_totals[name], reverse=True
  )

  return {"error": False, "assignees": sorted_assignees, "matrix": matrix}


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/api/data")
def get_data():
  data = fetch_asana_matrix()
  return jsonify(data)


if __name__ == "__main__":
  app.run(debug=True, port=5000)