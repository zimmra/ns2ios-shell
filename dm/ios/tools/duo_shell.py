"""Verify and stamp a game-free shell built with the native Duo hinge APIs."""
import argparse
import hashlib
import json
import plistlib
import zipfile
from pathlib import Path

PR = "https://github.com/seedds/nxnative/pull/683"
PR_HEAD = "6dff66b55d9c59e0c9df0119cc3ee1d4782f28c3"
SOURCE = "af294bd15e0f8a7e5c110140448c52412ec61c74"
BUILD_SUPPORT = "8e0916bf04f6fb8542c52ed01b166a8796158ca0"


def stamp(source, destination, sdk):
    version = tuple(int(x) for x in sdk.split("."))
    if version < (27, 1):
        raise ValueError("Native Duo hinge support requires the iOS 27.1 SDK or newer")
    with zipfile.ZipFile(source) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"Damaged shell archive: {bad}")
        root = "Payload/DmIOS.app/"
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate shell archive paths")
        for name in names:
            if name.startswith(root + "romfs") or any(
                name.startswith(root + part + "/") for part in ("msl", "aoc", "Frameworks")
            ) or name.lower().endswith((".nsp", ".xci", ".nca", ".keys", ".ipa")):
                raise ValueError(f"Shell contains game content: {name}")
        info = plistlib.loads(archive.read(root + "Info.plist"))
        landscape = {"UIInterfaceOrientationLandscapeLeft", "UIInterfaceOrientationLandscapeRight"}
        all_poses = landscape | {"UIInterfaceOrientationPortrait", "UIInterfaceOrientationPortraitUpsideDown"}
        if set(info.get("UISupportedInterfaceOrientations", [])) != landscape:
            raise ValueError("Ordinary iPhones and the Duo outer display must remain landscape-only")
        if set(info.get("UISupportedInterfaceOrientations~ipad", [])) != all_poses:
            raise ValueError("iPad orientation policy is incomplete")
        if "UIRequiresFullScreen" in info or "UILaunchStoryboardName" in info:
            raise ValueError("Legacy fullscreen or launch-storyboard compatibility blocks native rotation")
        if info.get("UILaunchScreen") != {}:
            raise ValueError("Native launch-screen configuration is missing")
        binary = archive.read(root + info["CFBundleExecutable"])
        for symbol in (b"UIHingeInteraction", b"reservedRegionsOfKind:options:", b"hingeChanged:"):
            if symbol not in binary:
                raise ValueError(f"Native hinge code was not compiled: {symbol.decode()}")
        proof = {
            "pull_request": PR,
            "pull_request_head": PR_HEAD,
            "shell_source": SOURCE,
            "build_support_source": BUILD_SUPPORT,
            "sdk": sdk,
            "native_hinge": True,
            "binary_sha256": hashlib.sha256(binary).hexdigest(),
        }
        stamp_name = root + "dm/duo_build.json"
        with zipfile.ZipFile(destination, "w") as output:
            for entry in archive.infolist():
                if entry.filename != stamp_name:
                    output.writestr(entry, archive.read(entry))
            output.writestr(stamp_name, json.dumps(proof, indent=2) + "\n")
    return proof


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--sdk", required=True)
    args = parser.parse_args()
    if args.source.resolve() == args.destination.resolve():
        parser.error("source and destination must differ")
    print(json.dumps(stamp(args.source, args.destination, args.sdk), indent=2))
