import os
from datetime import date
import numpy as np

from tab2_MD import build_design_results_text


def _get_entry_value(entry, default=""):
    if entry is None:
        return default
    try:
        value = entry.get()
    except Exception:
        return default
    if value is None:
        return default
    if isinstance(value, str):
        value = value.strip()
        return value if value != "" else default
    return str(value)


def _set_entry_value(entry, value):
    if entry is None:
        return
    try:
        entry.delete(0, "end")
        entry.insert(0, str(value))
    except Exception:
        return


def _parse_float(value):
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    text = text.replace("deg", "").replace("°", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _safe_format_float(value, decimals=2):
    if value is None:
        return ""
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return ""


def _compute_wrap_angle_deg(gv):
    if not hasattr(gv, "Theta"):
        return None
    if not isinstance(gv.Theta, np.ndarray):
        return None
    if gv.Theta.size == 0:
        return None
    wrap_angles = gv.Theta[-1, :] - gv.Theta[0, :]
    return float(np.degrees(np.max(wrap_angles)))


def build_design_info_text(app, gv):
    base_text = build_design_results_text(gv).rstrip()

    d_hub = None
    if hasattr(gv, "gd"):
        d_hub = gv.gd.get("D_hub")

    dist_method = ""
    if hasattr(app, "option"):
        try:
            dist_method = app.option.get().strip()
        except Exception:
            dist_method = ""

    wrap_angle_text = ""
    wrap_angle_deg = None
    if hasattr(app, "wrap_angle_var"):
        try:
            wrap_angle_text = app.wrap_angle_var.get().strip()
        except Exception:
            wrap_angle_text = ""

    if wrap_angle_text:
        wrap_angle_deg = _parse_float(wrap_angle_text)
    if wrap_angle_deg is None:
        wrap_angle_deg = _compute_wrap_angle_deg(gv)

    lean_angle_text = ""
    lean_angle_deg = None
    if hasattr(app, "lean_angle_deg_entry"):
        lean_angle_text = _get_entry_value(app.lean_angle_deg_entry, "")
        lean_angle_deg = _parse_float(lean_angle_text)

    le_shape = getattr(gv, "le_shape", "")
    te_shape = getattr(gv, "te_shape", "")

    le_thickness_mm = ""
    te_thickness_mm = ""
    thickness_mode = ""
    recommend_choice = ""
    calc_thickness_mm = None
    min_thickness_mm = None
    if hasattr(app, "tab7"):
        le_thickness_mm = _get_entry_value(getattr(app.tab7, "le_thickness_entry", None), "")
        te_thickness_mm = _get_entry_value(getattr(app.tab7, "te_thickness_entry", None), "")
        if hasattr(app.tab7, "thickness_mode_var"):
            try:
                thickness_mode = app.tab7.thickness_mode_var.get().strip()
            except Exception:
                thickness_mode = ""
        if hasattr(app.tab7, "recommend_choice_var"):
            try:
                recommend_choice = app.tab7.recommend_choice_var.get().strip()
            except Exception:
                recommend_choice = ""
        calc_thickness_mm = getattr(app.tab7, "_calc_thickness_mm", None)
        min_thickness_mm = getattr(app.tab7, "_min_thickness_mm", None)

    if not le_thickness_mm and getattr(gv, "e", 0):
        le_thickness_mm = _safe_format_float(gv.e * 1000, 2)
    if not te_thickness_mm and getattr(gv, "e_min", 0):
        te_thickness_mm = _safe_format_float(gv.e_min * 1000, 2)

    additional_lines = [
        "",
        "=" * 80,
        "ADDITIONAL DESIGN INFO",
        "=" * 80,
        f"Hub Outlet Diameter (D_hub): {_safe_format_float(d_hub, 4) if d_hub is not None else 'N/A'} m",
        f"Blade Angle Distribution Method: {dist_method if dist_method else 'N/A'}",
    ]

    if wrap_angle_deg is not None:
        additional_lines.append(f"Max Wrap Angle: {_safe_format_float(wrap_angle_deg, 2)} deg")
    else:
        additional_lines.append("Max Wrap Angle: N/A")

    if lean_angle_deg is not None:
        additional_lines.append(f"Lean Angle: {_safe_format_float(lean_angle_deg, 2)} deg")
    else:
        additional_lines.append("Lean Angle: Not applied")

    additional_lines.extend([
        f"LE Shape: {le_shape if le_shape else 'N/A'}",
        f"TE Shape: {te_shape if te_shape else 'N/A'}",
        f"Thickness at LE: {le_thickness_mm if le_thickness_mm else 'N/A'} mm",
        f"Thickness at TE: {te_thickness_mm if te_thickness_mm else 'N/A'} mm",
        f"Thickness Mode: {thickness_mode if thickness_mode else 'N/A'}",
    ])
    additional_lines.extend(["-" * 80])

    max_blade_length_val = _parse_float(_get_entry_value(getattr(app, "max_blade_length", None), ""))

    saved_values = {
        "pm_Hnp": _get_entry_value(getattr(app, "pm_Hnp_entry", None), ""),
        "pm_Qnp": _get_entry_value(getattr(app, "pm_Qnp_entry", None), ""),
        "tm_Hnt": _get_entry_value(getattr(app, "tm_Hnt_entry", None), ""),
        "Zrv": _get_entry_value(getattr(app, "Zrv_entry", None), ""),
        "Zp": _get_entry_value(getattr(app, "Zp_entry", None), ""),
        "max_blade_length": _safe_format_float(max_blade_length_val, 4),
        "no_streamlines": _get_entry_value(getattr(app, "no_streamlines_spinbox", None), ""),
        "D_hub": _safe_format_float(d_hub, 6) if d_hub is not None else "",
        "bad_distribution_method": dist_method,
        "wrap_angle_deg": _safe_format_float(wrap_angle_deg, 4) if wrap_angle_deg is not None else "",
        "lean_angle_deg": _safe_format_float(lean_angle_deg, 4) if lean_angle_deg is not None else "",
        "le_shape": le_shape,
        "te_shape": te_shape,
        "le_thickness_mm": le_thickness_mm,
        "te_thickness_mm": te_thickness_mm,
        "thickness_mode": thickness_mode,
        "recommend_choice": recommend_choice,
        "calc_thickness_mm": _safe_format_float(calc_thickness_mm, 4) if calc_thickness_mm is not None else "",
        "min_thickness_mm": _safe_format_float(min_thickness_mm, 4) if min_thickness_mm is not None else "",
    }

    values_lines = ["", "SAVED_VALUES_BEGIN"]
    for key, value in saved_values.items():
        values_lines.append(f"{key}={value}")
    values_lines.append("SAVED_VALUES_END")

    coord_lines = []
    control_points = getattr(gv, "bad_distribution_control_points", None)
    if isinstance(control_points, np.ndarray) and control_points.shape == (5, 2):
        coord_lines.append("BAD_DISTRIBUTION_COORDS_BEGIN")
        for point in control_points:
            coord_lines.append(f"{point[0]:.8f},{point[1]:.8f}")
        coord_lines.append("BAD_DISTRIBUTION_COORDS_END")

    return "\n".join([base_text] + additional_lines + values_lines + coord_lines) + "\n"


def write_design_info_file(app, gv, file_path):
    content = build_design_info_text(app, gv)
    with open(file_path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return file_path


def build_project_filename(gv):
    """Name the project using the local date and active operating condition."""
    values = (gv.heads["Hnp"], gv.flows["Qp"], gv.heads["Hnt"], gv.flows["Qt"])
    parts = [f"{float(value):.3f}".rstrip("0").rstrip(".") for value in values]
    return "_".join([date.today().isoformat(), *parts]) + ".txt"


def write_design_info_to_directory(app, gv, directory_path, filename=None):
    if filename is None:
        filename = build_project_filename(gv)
    file_path = os.path.join(directory_path, filename)
    return write_design_info_file(app, gv, file_path)


def parse_design_info_text(text):
    values = {}
    in_values = False
    in_coords = False
    coords = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == "SAVED_VALUES_BEGIN":
            in_values = True
            continue
        if line == "SAVED_VALUES_END":
            in_values = False
            continue
        if line == "BAD_DISTRIBUTION_COORDS_BEGIN":
            in_coords = True
            continue
        if line == "BAD_DISTRIBUTION_COORDS_END":
            in_coords = False
            continue
        if in_values:
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
            continue
        if in_coords:
            if "," not in line:
                continue
            x_text, y_text = line.split(",", 1)
            x_val = _parse_float(x_text)
            y_val = _parse_float(y_text)
            if x_val is None or y_val is None:
                continue
            coords.append([x_val, y_val])
    if coords:
        values["bad_distribution_control_points"] = coords
    return values


def apply_project_values(app, gv, values):
    _set_entry_value(getattr(app, "pm_Hnp_entry", None), values.get("pm_Hnp", ""))
    _set_entry_value(getattr(app, "pm_Qnp_entry", None), values.get("pm_Qnp", ""))
    _set_entry_value(getattr(app, "tm_Hnt_entry", None), values.get("tm_Hnt", ""))
    _set_entry_value(getattr(app, "Zrv_entry", None), values.get("Zrv", ""))
    _set_entry_value(getattr(app, "Zp_entry", None), values.get("Zp", ""))
    _set_entry_value(getattr(app, "no_streamlines_spinbox", None), values.get("no_streamlines", ""))
    _set_entry_value(getattr(app, "d_hub_entry", None), values.get("D_hub", ""))

    max_blade_length_val = _parse_float(values.get("max_blade_length"))
    if max_blade_length_val is not None and hasattr(app, "max_blade_length"):
        try:
            app.max_blade_length.set(max_blade_length_val)
        except Exception:
            pass
    if max_blade_length_val is not None and hasattr(app, "max_blade_length_str"):
        try:
            app.max_blade_length_str.set(f"{max_blade_length_val:.2f}")
        except Exception:
            pass

    if hasattr(app, "option") and values.get("bad_distribution_method"):
        try:
            app.option.set(values.get("bad_distribution_method"))
        except Exception:
            pass

    if hasattr(app, "wrap_angle_var") and values.get("wrap_angle_deg"):
        try:
            wrap_val = _parse_float(values.get("wrap_angle_deg"))
            if wrap_val is not None:
                app.wrap_angle_var.set(f"{wrap_val:.2f}°")
        except Exception:
            pass

    if hasattr(app, "lean_angle_deg_entry"):
        _set_entry_value(app.lean_angle_deg_entry, values.get("lean_angle_deg", ""))

    if hasattr(app, "tab7"):
        if values.get("le_shape") and hasattr(app.tab7, "le_shape_var"):
            app.tab7.le_shape_var.set(values.get("le_shape"))
            gv.le_shape = values.get("le_shape")
        if values.get("te_shape") and hasattr(app.tab7, "te_shape_var"):
            app.tab7.te_shape_var.set(values.get("te_shape"))
            gv.te_shape = values.get("te_shape")
        _set_entry_value(getattr(app.tab7, "le_thickness_entry", None), values.get("le_thickness_mm", ""))
        _set_entry_value(getattr(app.tab7, "te_thickness_entry", None), values.get("te_thickness_mm", ""))
        if values.get("thickness_mode") and hasattr(app.tab7, "thickness_mode_var"):
            app.tab7.thickness_mode_var.set(values.get("thickness_mode"))
            if hasattr(app.tab7, "_on_thickness_mode_change"):
                app.tab7._on_thickness_mode_change()

        recommend_choice = values.get("recommend_choice", "")
        calc_mm = _parse_float(values.get("calc_thickness_mm"))
        min_mm = _parse_float(values.get("min_thickness_mm"))
        if calc_mm is not None:
            app.tab7._calc_thickness_mm = calc_mm
        if min_mm is not None:
            app.tab7._min_thickness_mm = min_mm
        if recommend_choice and hasattr(app.tab7, "recommend_choice_var"):
            app.tab7._recommend_ready = True
            if hasattr(app.tab7, "_set_recommend_enabled"):
                app.tab7._set_recommend_enabled(True)
            app.tab7.recommend_choice_var.set(recommend_choice)
            if hasattr(app.tab7, "_on_recommend_choice"):
                app.tab7._on_recommend_choice()

        if hasattr(app.tab7, "_set_apply_enabled"):
            app.tab7._set_apply_enabled(True)

    d_hub_val = _parse_float(values.get("D_hub"))
    if d_hub_val is not None:
        gv.gd["D_hub"] = d_hub_val

    le_mm = _parse_float(values.get("le_thickness_mm"))
    te_mm = _parse_float(values.get("te_thickness_mm"))
    if le_mm is not None:
        gv.e = le_mm / 1000
    if te_mm is not None:
        gv.e_min = te_mm / 1000

    if values.get("bad_distribution_control_points") and hasattr(app, "tab4"):
        try:
            coords = np.array(values.get("bad_distribution_control_points"), dtype=float)
            if coords.shape == (5, 2):
                gv.bad_distribution_control_points = coords
            option = values.get("bad_distribution_method") or gv.bad_distribution_method or "UCu Distribution"
            gv.bad_distribution_method = option
            if hasattr(app, "option"):
                app.option.set(option)
        except Exception:
            pass


def validate_project_values(values):
    required_keys = [
        "pm_Hnp",
        "pm_Qnp",
        "tm_Hnt",
        "Zrv",
        "Zp",
        "max_blade_length",
        "no_streamlines",
        "D_hub",
        "bad_distribution_method",
        "le_shape",
        "te_shape",
        "le_thickness_mm",
        "te_thickness_mm",
        "thickness_mode",
    ]

    missing = []
    for key in required_keys:
        value = values.get(key)
        if value is None or str(value).strip() == "":
            missing.append(key)

    return (len(missing) == 0, missing)
