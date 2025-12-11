#!/usr/bin/env python3

import sys
import json
from service.logo_service import LogoService

class LogoController:
    MODE = {
        "DETECT": "detect",
        "OVERLAY": "overlay",
        "PROCESS": "process",
        "ALL": {"detect", "overlay", "process"}
    }

    DEFAULT_MODEL_PATH = "best.pt"
    DEFAULT_CONF_THRESHOLD = 0.25
    DEFAULT_SCALE_W = 1.0
    DEFAULT_SCALE_H = 1.0
    DEFAULT_MARGIN = 0
    DEFAULT_OFFSET_Y = 0

    def __init__(self):
        self.service = LogoService()

    def run(self, argv):
        if len(argv) < 2:
            self._print_usage_and_exit()
        mode = self._parse_mode(argv[1])
        if mode == self.MODE["DETECT"]:
            self._handle_detect(argv)
        elif mode == self.MODE["OVERLAY"]:
            self._handle_overlay(argv)
        elif mode == self.MODE["PROCESS"]:
            self._handle_process(argv)
        else:
            self._unknown_mode(mode)

    def _parse_mode(self, raw_mode):                                                                            
        return raw_mode if raw_mode in self.MODE["ALL"] else None

    def _handle_detect(self, argv):
        if len(argv) < 3:
            self._print_usage_and_exit()
        image_path = argv[2]
        model_path = argv[3] if len(argv) > 3 else self.DEFAULT_MODEL_PATH
        conf_threshold = float(argv[4]) if len(argv) > 4 else self.DEFAULT_CONF_THRESHOLD
        try:
            result = self.service.detect_logo(image_path, model_path, conf_threshold)
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({"logos": [], "count": 0, "error": str(e)}), file=sys.stderr)
            sys.exit(1)

    def _handle_overlay(self, argv):
        if len(argv) < 9:
            self._print_usage_and_exit()
        origin_path = argv[2]
        logo_path = argv[3]
        x, y = int(argv[4]), int(argv[5])
        width, height = int(argv[6]), int(argv[7                                                                                                                                                                                            ])
        output_path = argv[8]
        scale_w = float(argv[9]) if len(argv) > 9 else self.DEFAULT_SCALE_W
        scale_h = float(argv[10]) if len(argv) > 10 else scale_w
        margin = int(argv[11]) if len(argv) > 11 else self.DEFAULT_MARGIN
        offset_y = int(argv[12]) if len(argv) > 12 else self.DEFAULT_OFFSET_Y
        self._apply_overrides(scale_w, scale_h, margin, offset_y)
        try:
            result = self.service.overlay_logo(origin_path, logo_path, x, y, width, height, output_path)
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({"output": "", "error": str(e)}), file=sys.stderr)
            sys.exit(1)

    def _handle_process(self, argv):
        if len(argv) < 6:
            self._print_usage_and_exit()
        origin_path = argv[2]
        logo_path = argv[3]
        model_path = argv[4]
        if len(argv) >= 7:
            try:
                conf_threshold = float(argv[5])
                output_path = argv[6]
            except ValueError:
                conf_threshold = self.DEFAULT_CONF_THRESHOLD
                output_path = argv[5]
        else:
            conf_threshold = self.DEFAULT_CONF_THRESHOLD
            output_path = argv[5]
        scale_w = float(argv[7]) if len(argv) > 7 else self.DEFAULT_SCALE_W
        scale_h = float(argv[8]) if len(argv) > 8 else scale_w
        margin = int(argv[9]) if len(argv) > 9 else self.DEFAULT_MARGIN
        offset_y = int(argv[10]) if len(argv) > 10 else self.DEFAULT_OFFSET_Y
        self._apply_overrides(scale_w, scale_h, margin, offset_y)
        try:
            result = self.service.process_logo(origin_path, logo_path, model_path, conf_threshold, output_path)
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({"output": "", "error": str(e)}), file=sys.stderr)
            sys.exit(1)

    def _unknown_mode(self, mode):
        print(f"Unknown mode: {mode}", file=sys.stderr)
        print("Modes: detect, overlay, process", file=sys.stderr)
        sys.exit(1)

    def _print_usage_and_exit(self):
        print("Usage:", file=sys.stderr)
        print("  Detect only: logo_detect_overlay.py detect <image_path> [model_path] [conf_threshold]", file=sys.stderr)
        print("  Overlay only: logo_detect_overlay.py overlay <origin> <logo> <x> <y> <width> <height> <output> [scale_w] [scale_h] [margin] [offset_y]", file=sys.stderr)
        print("  Detect + Overlay: logo_detect_overlay.py process <origin> <logo> <model_path> [conf_threshold] <output> [scale_w] [scale_h] [margin] [offset_y]", file=sys.stderr)
        sys.exit(1)

    def _apply_overrides(self, scale_w, scale_h, margin, offset_y):
        LogoService.SCALE_W = scale_w
        LogoService.SCALE_H = scale_h
        LogoService.MARGIN = margin
        LogoService.OFFSET_Y = offset_y


def main():
    controller = LogoController()
    controller.run(sys.argv)


if __name__ == "__main__":
    main()
