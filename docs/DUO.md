# Native Duo shell build

The `Build native Duo shell` workflow builds the Windows packer's game-free
shell with [upstream PR 683](https://github.com/seedds/nxnative/pull/683), pinned
to `6dff66b55d9c59e0c9df0119cc3ee1d4782f28c3`. It uses shell release
`v0.0.0014`, source `af294bd15e0f8a7e5c110140448c52412ec61c74`, so the existing
release's Windows tools and profiles remain its matching packing inputs.
The snapshot omits `dm/mac/min_os.mk`, which its host Makefile includes even
for iOS project generation. The workflow restores that file from matching
upstream revision `8e0916bf04f6fb8542c52ed01b166a8796158ca0`.

The integration patch preserves the fork's runtime `DM_PAD_LAYOUT` setting.
Its frontend merge omits a cloud-save call absent from this shell release;
the Duo picture, input, orientation, safe-area and hinge changes are retained.
No game profile or shader translator is changed by the Duo patch.

The workflow uses the `xcode-27` runner and Xcode 27.1. It requires the native
`UIHingeInteraction.h` header, runs the orientation and shell-verification
checks, then builds the unsigned game-free device shell. Simulator input tests
are omitted at the owner's request after passing on the first integration run.
Operator-driven native rotation tests and physical-device game testing are
not performed by CI.

Download `native-duo-shell-pr683` from the successful workflow run. Its
`nxnative-duo-shell-pr683.zip` replaces the ordinary shell ZIP passed to
`scripts/nxn_pack.py`; game files and keys stay on the packing computer.
Repack each game, including previously built IPAs, to incorporate the new
frontend. Merely changing a game's settings or replacing its shader files
does not update the app executable.

The shell contains `dm/duo_build.json`, recording the source, PR, SDK and app
executable SHA-256. The build verifies the required native hinge symbols and
the phone/iPad orientation policy before writing this stamp. Each final IPA
should retain the stamp and exactly the same app executable hash. The packer
changes the game identity, resources and guest framework, not that executable.

On a physical Duo, check both outer-display landscape directions, both
inner-display portrait directions, landscape overlay and tabletop layout.
Confirm that the picture stays 16:9, controls remain usable, and changing pose
releases held touches. Existing app identifiers should be retained when
reinstalling to preserve each game's save location.
