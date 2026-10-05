"""Keep OrangeFox atomic DRM, selecting one full-width primary plane on MTK."""
import hashlib
import json
import pathlib
import sys

UPSTREAM_SHA256 = "41aba0485d2ac547bc136e756017dcddcd47b5741340d592120dd0d7b5baabd3"


def patch(source):
    source = source.replace(b"\r\n", b"\n")
    if hashlib.sha256(source).hexdigest() != UPSTREAM_SHA256:
        raise ValueError("DRM source changed upstream; review the MTK patch before rebuilding")
    text = source.decode("utf-8")

    def replace(old, new):
        nonlocal text
        if text.count(old) != 1:
            raise ValueError("Unexpected DRM source context: " + old[:80])
        text = text.replace(old, new)

    replace("if (!obj || obj->plane->plane_id != obj_id)",
            "if (!obj || !obj->plane || obj->plane->plane_id != obj_id)")
    helper = '''// MediaTek exposes a full-width primary plane. Hardware dual-pipe splitting
// is performed by the kernel, unlike the userspace SDE layer-mixer topology.
static drmModePlane* find_mtk_primary_plane(drmModePlaneRes* options,
                                          uint32_t crtc_mask) {
  for (uint32_t i = 0; i < options->count_planes; ++i) {
    drmModePlane* plane = drmModeGetPlane(drm_fd, options->planes[i]);
    if (!plane) continue;
    if (!(plane->possible_crtcs & crtc_mask)) {
      drmModeFreePlane(plane);
      continue;
    }
    bool primary = false;
    drmModeObjectProperties* props = drmModeObjectGetProperties(
        drm_fd, plane->plane_id, DRM_MODE_OBJECT_PLANE);
    if (props) {
      for (uint32_t j = 0; j < props->count_props; ++j) {
        drmModePropertyRes* prop = drmModeGetProperty(drm_fd, props->props[j]);
        if (!prop) continue;
        if (!strcmp(prop->name, "type") &&
            props->prop_values[j] == DRM_PLANE_TYPE_PRIMARY) primary = true;
        drmModeFreeProperty(prop);
      }
      drmModeFreeObjectProperties(props);
    }
    if (primary) return plane;
    drmModeFreePlane(plane);
  }
  return nullptr;
}

'''
    replace("static GRSurface* drm_init(minui_backend* backend __unused) {",
            helper + "static GRSurface* drm_init(minui_backend* backend __unused) {")
    replace("  disable_non_main_crtcs(drm_fd, res, main_monitor_crtc);", '''  drmVersionPtr driver = drmGetVersion(drm_fd);
  bool is_mediatek = driver && driver->name &&
      std::string(driver->name, driver->name_len) == "mediatek";
  if (driver) drmFreeVersion(driver);
  uint32_t main_crtc_mask = 0;
  for (int i = 0; i < res->count_crtcs && i < 32; ++i) {
    if (res->crtcs[i] == main_monitor_crtc->crtc_id) main_crtc_mask = 1U << i;
  }
  // Check before plane enumeration; MTK does not require two userspace planes.
  if (is_mediatek) number_of_lms = 1;

  disable_non_main_crtcs(drm_fd, res, main_monitor_crtc);''')
    replace('if (!strcmp(conn_res.props_info[j]->name, "mode_properties")) {',
            'if (!is_mediatek && !strcmp(conn_res.props_info[j]->name, "mode_properties")) {')
    replace('''  /* Set plane resources */
  for(uint32_t i = 0; i < number_of_lms; ++i) {
    plane_res[i].plane = drmModeGetPlane(drm_fd, plane_options->planes[i]);
    if (!plane_res[i].plane)
      return NULL;
  }''', '''  /* Set plane resources */
  if (is_mediatek) {
    plane_res[0].plane = find_mtk_primary_plane(plane_options, main_crtc_mask);
    if (!plane_res[0].plane) {
      printf("MTK DRM: no primary plane supports the active CRTC\\n");
      drmModeFreePlaneResources(plane_options);
      return NULL;
    }
    printf("MTK atomic DRM: full-width primary plane %u, CRTC %u, %dx%d\\n",
           plane_res[0].plane->plane_id, main_monitor_crtc->crtc_id, width, height);
  } else {
    for(uint32_t i = 0; i < number_of_lms; ++i) {
      plane_res[i].plane = drmModeGetPlane(drm_fd, plane_options->planes[i]);
      if (!plane_res[i].plane)
        return NULL;
    }
  }''')
    return text.encode("utf-8")


if __name__ == "__main__":
    path = pathlib.Path(sys.argv[1])
    result = patch(path.read_bytes())
    path.write_bytes(result)
    report = {"backend": "OrangeFox atomic DRM with MTK full-width primary-plane patch",
              "upstream_sha256": UPSTREAM_SHA256,
              "patched_sha256": hashlib.sha256(result).hexdigest(),
              "patch": "scripts/patch-mtk-drm.py", "device_test_passed": False}
    print(json.dumps(report, indent=2))
