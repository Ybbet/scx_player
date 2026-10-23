from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from . import __version__
from .config import Config
from .daemon import Player
from .state import PlayerState


def main() -> int:
    parser = argparse.ArgumentParser(prog="scoralyx-player", description="Client Linux Scoralyx")
    parser.add_argument("--version", action="version", version=f"Scoralyx Player {__version__}")
    parser.add_argument("--config", type=Path, help="Fichier de configuration TOML")
    parser.add_argument("--verbose", action="store_true", help="Activer les journaux de diagnostic")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="Lancer le service Player")
    status = sub.add_parser("status", help="Afficher l'état local de l'enrôlement")
    status.add_argument("--json", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        config = Config.load(args.config)
        if args.command == "status":
            state = PlayerState.load(config.state_path)
            output = {
                "installation_id": state.installation_id,
                "machine_name": config.machine_name,
                "pairing_code": state.pairing_code or None,
                "enrolled": bool(state.token),
                "screen_id": state.screen_id or None,
                "screen_name": state.screen_name or None,
                "configuration_version": state.configuration_version,
            }
            print(json.dumps(output, ensure_ascii=False, indent=2) if args.json else "\n".join(f"{key}: {value}" for key, value in output.items()))
            return 0
        Player(config).run()
    except (OSError, ValueError) as error:
        logging.error("%s", error)
        return 2
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())

