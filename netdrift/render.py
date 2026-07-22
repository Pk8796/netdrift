from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader


def render_all(
    vars_file="devices.vars.yml",
    template_dir="templates",
    template="frr.cfg.j2",
    out_dir="intended",
):
    data = yaml.safe_load(Path(vars_file).read_text())
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tmpl = env.get_template(template)

    Path(out_dir).mkdir(exist_ok=True)
    written = []
    for name, model in data["devices"].items():
        rendered = tmpl.render(name=name, **model).rstrip() + "\n"
        path = Path(out_dir, f"{name}.cfg")
        path.write_text(rendered)
        written.append(path)
    return written
